import time
import tempfile
import structlog
from pathlib import Path
import random

from app.db.base import Base # Ensure all mappers are initialized
from app.db.session import SessionLocal
from app.services.document import KnowledgeService

logger = structlog.get_logger()

HEARTBEAT_FILE = Path(tempfile.gettempdir()) / "aina_worker_heartbeat"

def write_heartbeat() -> None:
    try:
        HEARTBEAT_FILE.write_text(str(time.time()), encoding="utf-8")
    except Exception as e:
        logger.error("failed_to_write_heartbeat_file", error=str(e))

def check_stuck_jobs() -> None:
    db = SessionLocal()
    try:
        from datetime import datetime, timezone, timedelta
        from app.models.document import KnowledgeJob, KnowledgeJobStatus, KnowledgeSource, SourceStatus
        
        # Stuck threshold of 30 minutes
        stuck_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        stuck_jobs = db.query(KnowledgeJob).filter(
            KnowledgeJob.status == KnowledgeJobStatus.PROCESSING,
            KnowledgeJob.started_at < stuck_threshold
        ).all()
        
        for job in stuck_jobs:
            logger.error(
                "stuck_job_detected",
                job_id=str(job.id),
                started_at=str(job.started_at),
                attempts=job.attempts
            )
            # Reset status so it is re-queued, or fail if it reached max attempts
            if job.attempts >= job.max_attempts:
                job.status = KnowledgeJobStatus.FAILED
                job.error_message = "Job timed out in PROCESSING state."
                source = db.query(KnowledgeSource).filter(KnowledgeSource.id == job.source_id).first()
                if source:
                    source.status = SourceStatus.FAILED
                    source.error_message = "Job timed out in PROCESSING state."
            else:
                job.status = KnowledgeJobStatus.QUEUED
                job.error_message = f"Job timed out in PROCESSING state. Re-queued (attempt {job.attempts}/{job.max_attempts})."
            
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("failed_to_check_stuck_jobs", error=str(e), exc_info=True)
    finally:
        db.close()

def run_once() -> bool:
    db = SessionLocal()
    try:
        return KnowledgeService.process_next_job(db)
    finally:
        db.close()

def main() -> None:
    logger.info("Knowledge worker started.")
    backoff = 2  # seconds
    MAX_BACKOFF = 60
    last_stuck_check = 0.0

    while True:
        try:
            # 1. Update heartbeat file
            write_heartbeat()
            
            # 2. Run stuck job check every 60 seconds
            now = time.monotonic()
            if now - last_stuck_check > 60.0:
                check_stuck_jobs()
                last_stuck_check = now

            # 3. Process next job
            did_work = run_once()
            backoff = 2  # Reset backoff on successful loop execution
            
            if not did_work:
                time.sleep(2)
        except Exception as e:
            logger.error("worker_loop_exception", error=str(e), backoff_seconds=backoff, exc_info=True)
            time.sleep(backoff + random.uniform(0.0, 1.0))
            backoff = min(backoff * 2, MAX_BACKOFF)

if __name__ == "__main__":
    main()
