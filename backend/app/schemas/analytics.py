import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

# --- KPI metrics ---
class KPIMetric(BaseModel):
    value: float
    change_pct: float

class KPIResponse(BaseModel):
    total_conversations: KPIMetric
    avg_response_time: KPIMetric
    satisfaction_score: KPIMetric
    workload_reduction: KPIMetric

# --- Charts and Breakdowns ---
class VolumeSeriesItem(BaseModel):
    date: date
    conversations: int
    messages: int

class LanguageMixItem(BaseModel):
    language: str
    count: int

class ChannelPerfItem(BaseModel):
    channel: str
    count: int

class InteractionItem(BaseModel):
    id: uuid.UUID
    chatbot_id: uuid.UUID
    chatbot_name: str
    status: str
    total_messages: int
    started_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Agent replies ---
class AgentReplyRequest(BaseModel):
    message: str
