import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db, require_role, get_current_org_id
from app.services.api_key import ApiKeyService
from app.schemas.api_key import (
    ApiKeyResponse,
    ApiKeyCreateRequest,
    ApiKeyCreateResponse
)

router = APIRouter(prefix="/settings/api-keys", tags=["API Key Settings"])


@router.get("", response_model=List[ApiKeyResponse])
def list_keys(
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """List all API keys for the active organization."""
    return ApiKeyService.list_keys(db, org_id)


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_key(
    key_in: ApiKeyCreateRequest,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(require_role("owner", "admin"))
):
    """Generate a new secure API key. Requires owner or admin role."""
    return ApiKeyService.create_key(db, org_id, key_in.name)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(require_role("owner", "admin"))
):
    """Revoke an API key. Requires owner or admin role."""
    ApiKeyService.revoke_key(db, org_id, key_id)
    return None
