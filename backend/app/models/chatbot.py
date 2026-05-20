import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class ChatbotStatus(str, PyEnum):
    DRAFT = "draft"
    TRAINING = "training"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Chatbot(Base):
    __tablename__ = "chatbots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="RESTRICT"), nullable=False)
    total_conversations = Column(Integer, nullable=False, default=0)
    total_messages = Column(Integer, nullable=False, default=0)
    status = Column(
        Enum(ChatbotStatus, name="enum_chatbot_status"),
        nullable=False,
        default=ChatbotStatus.DRAFT
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    persona = relationship("Persona", back_populates="chatbots")
    organization = relationship("Organization")

    __table_args__ = (
        Index("idx_chatbots_active", "id", postgresql_where=(deleted_at == None)),
    )
