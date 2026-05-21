import uuid
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class Channel(str, PyEnum):
    WHATSAPP = "whatsapp"
    WEB = "web"


class ConversationStatus(str, PyEnum):
    ONGOING = "ongoing"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class MessageRole(str, PyEnum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False)
    channel = Column(
        Enum(Channel, name="enum_channel"),
        nullable=False,
        default=Channel.WEB
    )

    # Relationships
    chatbot = relationship("Chatbot")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id", ondelete="SET NULL"), nullable=True)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(
        Enum(ConversationStatus, name="enum_conversation_status"),
        nullable=False,
        default=ConversationStatus.ONGOING
    )
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    chatbot = relationship("Chatbot")
    deployment = relationship("Deployment")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id])

    __table_args__ = (
        Index("idx_conversations_active", "id", postgresql_where=(deleted_at == None)),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    config_id = Column(UUID(as_uuid=True), ForeignKey("ai_model_configs.id", ondelete="SET NULL"), nullable=True)
    role = Column(
        Enum(MessageRole, name="enum_message_role"),
        nullable=False
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), primary_key=True, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation")
    config = relationship("AIModelConfig")
