import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Enum, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base

class AuthProvider(str, PyEnum):
    EMAIL = "email"
    GOOGLE = "google"
    SAML = "saml"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    auth_provider = Column(
        Enum(AuthProvider, name="enum_auth_provider"),
        nullable=False,
        default=AuthProvider.EMAIL
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    memberships = relationship("OrgMember", back_populates="user", cascade="all, delete-orphan")
    owned_organizations = relationship("Organization", back_populates="owner")

    __table_args__ = (
        Index("idx_users_active", "id", postgresql_where=(deleted_at == None)),
        Index("uq_users_email_lower", text("lower(email)"), unique=True),
    )
