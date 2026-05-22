import uuid
from sqlalchemy import Column, Integer, Date, Float, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.conversation import Channel

class AnalyticsDaily(Base):
    __tablename__ = "analytics_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="RESTRICT"), nullable=False)
    stat_date = Column(Date, nullable=False)
    total_conversations = Column(Integer, nullable=False, default=0)
    total_messages = Column(Integer, nullable=False, default=0)
    avg_response_time = Column(Float, nullable=True)  # in seconds
    avg_sentiment = Column(Float, nullable=True)  # scale e.g. 0 to 5 or -1 to 1
    escalated_count = Column(Integer, nullable=False, default=0)
    resolved_count = Column(Integer, nullable=False, default=0)

    # Relationships
    chatbot = relationship("Chatbot")
    channels = relationship("AnalyticsByChannel", back_populates="analytics_daily", cascade="all, delete-orphan")
    languages = relationship("AnalyticsByLang", back_populates="analytics_daily", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("chatbot_id", "stat_date", name="uq_analytics_chatbot_date"),
        Index("idx_analytics_chatbot_date", "chatbot_id", "stat_date"),
    )


class AnalyticsByChannel(Base):
    __tablename__ = "analytics_by_channel"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analytics_daily_id = Column(UUID(as_uuid=True), ForeignKey("analytics_daily.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), nullable=False)  # WhatsApp, Web
    count = Column(Integer, nullable=False, default=0)

    # Relationships
    analytics_daily = relationship("AnalyticsDaily", back_populates="channels")

    __table_args__ = (
        UniqueConstraint("analytics_daily_id", "channel", name="uq_analytics_channel"),
        Index("idx_analytics_by_channel_daily", "analytics_daily_id"),
    )


class AnalyticsByLang(Base):
    __tablename__ = "analytics_by_lang"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analytics_daily_id = Column(UUID(as_uuid=True), ForeignKey("analytics_daily.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(30), nullable=False)  # English, Urdu, Roman Urdu
    count = Column(Integer, nullable=False, default=0)

    # Relationships
    analytics_daily = relationship("AnalyticsDaily", back_populates="languages")

    __table_args__ = (
        UniqueConstraint("analytics_daily_id", "language", name="uq_analytics_lang"),
        Index("idx_analytics_by_lang_daily", "analytics_daily_id"),
    )
