import uuid
from enum import Enum as PyEnum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index, Text, BigInteger, UniqueConstraint, ForeignKeyConstraint, text, FetchedValue
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from pgvector.sqlalchemy import Vector
from app.core.config import settings

class SourceType(str, PyEnum):
    FILE = "file"
    TEXT = "text"
    WEBSITE = "website"
    EMAIL = "email"
    PHONE = "phone"
    APP = "app"

class SourceStatus(str, PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"

class FileType(str, PyEnum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"

class ChunkStatus(str, PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class KnowledgeJobStatus(str, PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatbot_id = Column(UUID(as_uuid=True), nullable=False)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    source_type = Column(Enum(SourceType, name="enum_source_type"), nullable=False)
    label = Column(String(120), nullable=False)
    value = Column(Text, nullable=False)
    status = Column(Enum(SourceStatus, name="enum_source_status"), nullable=False, default=SourceStatus.QUEUED)
    error_message = Column(Text, nullable=True)
    pages_crawled = Column(Integer, nullable=True)
    total_content_chars = Column(Integer, nullable=True)
    crawl_duration_secs = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="source", cascade="all, delete-orphan")
    document = relationship("Document", uselist=False, back_populates="source", cascade="all, delete-orphan")
    jobs = relationship("KnowledgeJob", back_populates="source", cascade="all, delete-orphan")

    @property
    def is_searchable(self) -> bool:
        return self.source_type in {SourceType.FILE, SourceType.TEXT, SourceType.WEBSITE}

    __table_args__ = (
        ForeignKeyConstraint(
            ["chatbot_id", "org_id"],
            ["chatbots.id", "chatbots.org_id"],
            name="fk_knowledge_sources_chatbot_org",
            ondelete="CASCADE",
        ),
        UniqueConstraint("id", "chatbot_id", "org_id", name="uq_knowledge_sources_id_chatbot_org"),
        Index("idx_knowledge_sources_chatbot_id", "chatbot_id"),
        Index("idx_knowledge_sources_org_id", "org_id"),
    )

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    chatbot_id = Column(UUID(as_uuid=True), nullable=False)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    file_type = Column(Enum(FileType, name="enum_file_type"), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False)

    source = relationship("KnowledgeSource", back_populates="document")

    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "chatbot_id", "org_id"],
            ["knowledge_sources.id", "knowledge_sources.chatbot_id", "knowledge_sources.org_id"],
            name="fk_documents_source_chatbot_org",
            ondelete="CASCADE",
        ),
        Index("idx_documents_source_id", "source_id"),
    )

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    index_status = Column(Enum(ChunkStatus, name="enum_chunk_status"), nullable=False, default=ChunkStatus.QUEUED)
    embedding = Column(Vector(settings.EMBEDDING_DIM), nullable=True)
    text_search_vector = Column(TSVECTOR, FetchedValue(), nullable=True)
    token_count = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    metadata_extra = Column(JSONB, nullable=False, server_default=text("'{}'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    source = relationship("KnowledgeSource", back_populates="chunks")
    document = relationship("Document")

    __table_args__ = (
        UniqueConstraint("source_id", "chunk_index", name="uq_knowledge_chunks_source_chunk"),
        Index("idx_chunks_chatbot_status", "chatbot_id", "index_status"),
        Index("idx_chunks_source_index", "source_id", "chunk_index"),
    )


class KnowledgeJob(Base):
    __tablename__ = "knowledge_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    chatbot_id = Column(UUID(as_uuid=True), nullable=False)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Enum(KnowledgeJobStatus, name="enum_knowledge_job_status"), nullable=False, default=KnowledgeJobStatus.QUEUED)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    retry_after = Column(DateTime(timezone=True), nullable=True)

    source = relationship("KnowledgeSource", back_populates="jobs")

    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "chatbot_id", "org_id"],
            ["knowledge_sources.id", "knowledge_sources.chatbot_id", "knowledge_sources.org_id"],
            name="fk_knowledge_jobs_source_chatbot_org",
            ondelete="CASCADE",
        ),
    )
