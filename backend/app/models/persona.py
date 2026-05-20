import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class Persona(Base):
    __tablename__ = "personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)  # NULL = Built-in system persona
    name = Column(String(80), nullable=False)
    language = Column(String(30), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    traits = relationship("PersonaTrait", back_populates="persona", cascade="all, delete-orphan")
    chatbots = relationship("Chatbot", back_populates="persona")

    __table_args__ = (
        Index("idx_personas_active", "id", postgresql_where=(deleted_at == None)),
    )


class PersonaTrait(Base):
    __tablename__ = "persona_traits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False)
    trait_name = Column(String(80), nullable=False)

    # Relationships
    persona = relationship("Persona", back_populates="traits")
