import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str                    # e.g., "ak_prod_xxxx"
    created_at: datetime
    last_used: Optional[datetime] = None
    status: str                    # "active" or "revoked"

    model_config = ConfigDict(from_attributes=True)

class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class ApiKeyCreateResponse(BaseModel):
    id: uuid.UUID
    name: str
    key: str                       # full key, shown ONCE
    prefix: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
