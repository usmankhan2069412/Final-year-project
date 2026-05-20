import uuid
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
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
    encrypted_api_key = Column(Text, nullable=False)
    secret_ref = Column(String(255), nullable=True)

    # Relationships
    provider = relationship("AIProvider", back_populates="configs")
    organization = relationship("Organization")
    routing_rules = relationship("RoutingRule", back_populates="config", cascade="all, delete-orphan")


class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("ai_model_configs.id", ondelete="CASCADE"), nullable=False)
    intent = Column(String(80), nullable=False)
    model_target = Column(String(80), nullable=False)

    # Relationships
    config = relationship("AIModelConfig", back_populates="routing_rules")
