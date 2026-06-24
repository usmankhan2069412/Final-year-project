import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.message_job import MessageJob, MessageJobStatus


logger = logging.getLogger(__name__)


class OutboxService:
    @staticmethod
    def enqueue(
        db: Session,
        conversation_id: uuid.UUID,
        channel: str,
        payload: Dict[str, Any],
    ) -> MessageJob:
        job = MessageJob(
            conversation_id=conversation_id,
            channel=channel,
            payload=payload,
            status=MessageJobStatus.QUEUED,
        )
        db.add(job)
        db.flush()
        logger.info("Enqueued MessageJob %s for channel=%s", job.id, channel)
        return job

    @classmethod
    def process_next_job(cls, db: Session) -> bool:
        now = datetime.now(timezone.utc)
        job = (
            db.query(MessageJob)
            .filter(
                MessageJob.status == MessageJobStatus.QUEUED,
                MessageJob.attempts < MessageJob.max_attempts,
                or_(
                    MessageJob.retry_after == None,
                    MessageJob.retry_after <= now,
                ),
            )
            .order_by(MessageJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .first()
        )
        if not job:
            return False

        job.status = MessageJobStatus.PROCESSING
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        job.error_message = None
        db.commit()

        channel = job.channel

        try:
            if channel == "whatsapp":
                from app.services.whatsapp import WhatsAppService
                payload = job.payload
                WhatsAppService.send_whatsapp_message(
                    phone_number=payload["phone_number"],
                    text=payload["text"],
                    phone_number_id=payload["phone_number_id"],
                )
            else:
                raise ValueError(f"Unsupported outbound channel: {channel}")

            job.status = MessageJobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info("MessageJob %s completed for channel=%s", job.id, channel)
            return True

        except Exception as exc:
            db.rollback()
            job = db.query(MessageJob).filter(MessageJob.id == job.id).first()
            if job:
                job.error_message = str(exc)
                if job.attempts >= job.max_attempts:
                    job.status = MessageJobStatus.FAILED
                    logger.error(
                        "MessageJob %s FAILED after %d attempts: %s",
                        job.id, job.attempts, exc,
                    )
                else:
                    job.status = MessageJobStatus.QUEUED
                    backoff_seconds = 30 * (2 ** (job.attempts - 1))
                    job.retry_after = datetime.now(timezone.utc) + timedelta(
                        seconds=min(backoff_seconds, 3600)
                    )
                    logger.warning(
                        "MessageJob %s will retry in %ds (attempt %d/%d): %s",
                        job.id,
                        min(backoff_seconds, 3600),
                        job.attempts,
                        job.max_attempts,
                        exc,
                    )
            db.commit()
            return True
