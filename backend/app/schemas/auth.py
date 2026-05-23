from datetime import datetime
from typing import Optional
import uuid
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Highly standard, permissive HTML5 email regex — allows all valid/normal email structures
_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _validate_and_normalize_email(v: str) -> str:
    """Strip, lowercase, then validate email. Shared across schemas."""
    clean = v.strip().lower()
    if not _EMAIL_REGEX.match(clean):
        raise ValueError("Invalid email format")
    return clean



class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_and_normalize_email(v)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        # Normalize only — do NOT expose format errors here (prevents user enumeration on login)
        return v.strip().lower()


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    auth_provider: str
    # deleted_at is intentionally excluded — never expose soft-delete state to clients

    model_config = ConfigDict(from_attributes=True)


class OrgResponse(BaseModel):
    id: uuid.UUID
    slug: str
    owner_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class UserMeResponse(BaseModel):
    user: UserResponse
    active_organization: OrgResponse


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_and_normalize_email(v)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")

    @field_validator("token")
    @classmethod
    def strip_token(cls, v: str) -> str:
        return v.strip()


class GoogleLoginRequest(BaseModel):
    token: str = Field(..., description="The ID token received from Google")


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    org_slug: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _validate_and_normalize_email(v)


class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")


