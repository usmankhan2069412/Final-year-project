import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.document import SourceType, SourceStatus, ChunkStatus, KnowledgeJobStatus

class KnowledgeSourceCreate(BaseModel):
    chatbot_id: uuid.UUID
    source_type: SourceType
    label: str
    value: str

class KnowledgeChunkResponse(BaseModel):
    id: uuid.UUID
    chunk_index: int
    index_status: ChunkStatus
    model_config = ConfigDict(from_attributes=True)

class KnowledgeSourceResponse(BaseModel):
    id: uuid.UUID
    chatbot_id: uuid.UUID
    source_type: SourceType
    label: str
    value: str
    status: SourceStatus
    error_message: Optional[str] = None
    is_searchable: bool
    pages_crawled: Optional[int] = None
    total_content_chars: Optional[int] = None
    crawl_duration_secs: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class KnowledgeSourceDetailResponse(KnowledgeSourceResponse):
    chunks: List[KnowledgeChunkResponse] = []

class KnowledgeJobResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    chatbot_id: uuid.UUID
    status: KnowledgeJobStatus
    attempts: int
    max_attempts: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
