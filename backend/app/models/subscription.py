import uuid
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(60), unique=True, nullable=False)
    price_pkr = Column(Numeric(10, 2), nullable=False)
    max_bots = Column(Integer, nullable=True)  # None = unlimited
    max_messages_per_month = Column(Integer, nullable=True)  # None = unlimited
    max_members = Column(Integer, nullable=True)  # None = unlimited
    features = Column(JSONB, nullable=False, default=list)
    is_popular = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), nullable=False, default="active")  # 'active', 'cancelled', 'past_due', 'trialing'
    period_start = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    period_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    org = relationship("Organization")

    __table_args__ = (
        Index("uq_subscriptions_active", "org_id", unique=True, postgresql_where=(status.in_(['active', 'trialing', 'past_due']))),
    )
