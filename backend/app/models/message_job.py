import uuid
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import enum

from app.db.session import Base

class MessageJobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class MessageJob(Base):
    __tablename__ = "message_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    channel = Column(String, index=True, nullable=False) # e.g. "whatsapp", "web"
    payload = Column(JSON, nullable=False) # e.g. {"phone_number": "+123", "text": "hello", "phone_number_id": "123"}
    
    status = Column(Enum(MessageJobStatus), default=MessageJobStatus.QUEUED, index=True)
    
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    retry_after = Column(DateTime(timezone=True), nullable=True, index=True)
