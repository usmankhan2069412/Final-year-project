import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, Text, UniqueConstraint, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class AIProvider(Base):
    __tablename__ = "ai_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)

    # Relationships
    configs = relationship("AIModelConfig", back_populates="provider", cascade="all, delete-orphan")


class AIModelConfig(Base):
    __tablename__ = "ai_model_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(80), nullable=False, default="default")
    display_name = Column(String(120), nullable=True)
    encrypted_api_key = Column(Text, nullable=False)
    secret_ref = Column(String(255), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    provider = relationship("AIProvider", back_populates="configs")
    organization = relationship("Organization")
    routing_rules = relationship("RoutingRule", back_populates="config", cascade="all, delete-orphan", foreign_keys="[RoutingRule.config_id]")

    __table_args__ = (
        UniqueConstraint("org_id", "provider_id", "model_name", name="uq_ai_model_configs_org_provider_model"),
        UniqueConstraint("id", "org_id", name="uq_ai_model_configs_id_org"),
    )


class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("ai_model_configs.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=True)
    intent = Column(String(80), nullable=False)
    model_override = Column(String(255), nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    fallback_config_id = Column(UUID(as_uuid=True), ForeignKey("ai_model_configs.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    config = relationship("AIModelConfig", back_populates="routing_rules", foreign_keys=[config_id])
    fallback_config = relationship("AIModelConfig", foreign_keys=[fallback_config_id])
