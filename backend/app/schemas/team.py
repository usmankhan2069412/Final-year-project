import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.auth import _validate_and_normalize_email

class TeamMemberResponse(BaseModel):
    id: uuid.UUID                       # org_member.id
    user_id: uuid.UUID
    name: Optional[str]
    email: str
    role: str                      # 'owner', 'admin', 'member'
    joined_at: datetime
    avatar: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class InviteMemberRequest(BaseModel):
    email: str
    role: str = Field(default="member", pattern="^(admin|member)$")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_and_normalize_email(v)

class UpdateRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|member)$")
