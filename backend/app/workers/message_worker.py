import time
import tempfile
import structlog
from pathlib import Path
import random

from app.db.base import Base
from app.db.session import SessionLocal
from app.services.outbox import OutboxService

logger = structlog.get_logger()

HEARTBEAT_FILE = Path(tempfile.gettempdir()) / "aina_message_worker_heartbeat"

def write_heartbeat() -> None:
    try:
        HEARTBEAT_FILE.write_text(str(time.time()), encoding="utf-8")
    except Exception as e:
        logger.error("failed_to_write_message_heartbeat", error=str(e))

def check_stuck_jobs() -> None:
    db = SessionLocal()
    try:
        from datetime import datetime, timezone, timedelta
        from app.models.message_job import MessageJob, MessageJobStatus

        stuck_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)

        stuck_jobs = db.query(MessageJob).filter(
            MessageJob.status == MessageJobStatus.PROCESSING,
            MessageJob.started_at < stuck_threshold
        ).all()

        for job in stuck_jobs:
            logger.error(
                "stuck_message_job_detected",
                job_id=str(job.id),
                started_at=str(job.started_at),
                attempts=job.attempts
            )
            if job.attempts >= job.max_attempts:
                job.status = MessageJobStatus.FAILED
                job.error_message = "Job timed out in PROCESSING state."
            else:
                job.status = MessageJobStatus.QUEUED
                job.error_message = f"Job timed out in PROCESSING state. Re-queued (attempt {job.attempts}/{job.max_attempts})."

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("failed_to_check_stuck_message_jobs", error=str(e), exc_info=True)
    finally:
        db.close()

def run_once() -> bool:
    db = SessionLocal()
    try:
        return OutboxService.process_next_job(db)
    finally:
        db.close()

def main() -> None:
    logger.info("Message worker started.")
    backoff = 2
    MAX_BACKOFF = 60
    last_stuck_check = 0.0

    while True:
        try:
            write_heartbeat()

            now = time.monotonic()
            if now - last_stuck_check > 60.0:
                check_stuck_jobs()
                last_stuck_check = now

            did_work = run_once()
            backoff = 2

            if not did_work:
                time.sleep(2)
        except Exception as e:
            logger.error("message_worker_loop_exception", error=str(e), backoff_seconds=backoff, exc_info=True)
            time.sleep(backoff + random.uniform(0.0, 1.0))
            backoff = min(backoff * 2, MAX_BACKOFF)

if __name__ == "__main__":
    main()
