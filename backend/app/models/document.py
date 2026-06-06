import uuid
from enum import Enum as PyEnum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship
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
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(Enum(SourceType, name="enum_source_type"), nullable=False)
    label = Column(String(120), nullable=False)
    value = Column(Text, nullable=False)
    status = Column(Enum(SourceStatus, name="enum_source_status"), nullable=False, default=SourceStatus.QUEUED)
    error_message = Column(Text, nullable=True)
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

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False, unique=True)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    file_type = Column(Enum(FileType, name="enum_file_type"), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False)

    source = relationship("KnowledgeSource", back_populates="document")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    index_status = Column(Enum(ChunkStatus, name="enum_chunk_status"), nullable=False, default=ChunkStatus.QUEUED)
    embedding = Column(Vector(settings.EMBEDDING_DIM), nullable=True)
    text_search_vector = Column(TSVECTOR, nullable=True)

    source = relationship("KnowledgeSource", back_populates="chunks")


class KnowledgeJob(Base):
    __tablename__ = "knowledge_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
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
