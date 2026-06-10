import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Text, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.session import Base
from app.core.config import settings

class SemanticCache(Base):
    __tablename__ = "semantic_caches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False)
    
    query_text = Column(Text, nullable=False)
    query_hash = Column(String(64), nullable=False)
    query_embedding = Column(Vector(settings.EMBEDDING_DIM), nullable=False)
    embedding_model = Column(String(100), nullable=False)
    
    response_text = Column(Text, nullable=False)
    source_chunk_ids = Column(JSONB, nullable=True)
    source_document_ids = Column(JSONB, nullable=True)
    
    knowledge_base_version = Column(Integer, nullable=False)
    persona_version = Column(Integer, nullable=False)
    
    hit_count = Column(Integer, nullable=False, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    chatbot = relationship("Chatbot")
    organization = relationship("Organization")

    __table_args__ = (
        UniqueConstraint('org_id', 'chatbot_id', 'query_hash', 'knowledge_base_version', 'persona_version', name='uq_semantic_cache_query'),
        Index("idx_semantic_cache_active", "chatbot_id", "is_active", "expires_at"),
    )
