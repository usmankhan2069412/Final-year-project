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
    res = ApiKeyService.create_key(db, org_id, key_in.name)
    from app.services.notification import NotificationService
    NotificationService.create_notification(
        db,
        user_id=current_user.id,
        title="API Key Created",
        details=f'API key "{key_in.name}" was created.'
    )
    return res


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(require_role("owner", "admin"))
):
    """Revoke an API key. Requires owner or admin role."""
    from app.models.api_key import ApiKey
    db_key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.org_id == org_id).first()
    key_name = db_key.name if db_key else "Unknown Key"

    ApiKeyService.revoke_key(db, org_id, key_id)

    from app.services.notification import NotificationService
    NotificationService.create_notification(
        db,
        user_id=current_user.id,
        title="API Key Revoked",
        details=f'API key "{key_name}" has been revoked.'
    )
    return None
