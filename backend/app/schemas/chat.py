import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.conversation import MessageRole, ConversationStatus

# --- Messages ---
class MessageBase(BaseModel):
    role: MessageRole
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: uuid.UUID
    conversation_id: uuid.UUID
    config_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Conversations ---
class ConversationBase(BaseModel):
    chatbot_id: uuid.UUID
    deployment_id: Optional[uuid.UUID] = None
    assigned_agent_id: Optional[uuid.UUID] = None
    status: ConversationStatus = ConversationStatus.ONGOING


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: uuid.UUID
    started_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Chat Interaction (API-facing) ---
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[uuid.UUID] = None  # If omitted, a new conversation is initialized


class SourceChunkInfo(BaseModel):
    chunk_id: uuid.UUID
    source_id: uuid.UUID
    text: str
    score: float


class ChatResponse(BaseModel):
    response: str
    conversation_id: uuid.UUID
    sources: List[SourceChunkInfo] = []
    status: ConversationStatus
