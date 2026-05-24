import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    details: str
    read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    details: str = Field(..., min_length=1, max_length=1000)
