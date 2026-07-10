import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant_db, require_role, get_current_org_id
from app.services.api_key import ApiKeyService
from app.models.api_key import ApiKey
from app.schemas.api_key import (
    ApiKeyResponse,
    ApiKeyCreateRequest,
    ApiKeyCreateResponse
)

router = APIRouter(prefix="/settings/api-keys", tags=["API Key Settings"])


@router.get("", response_model=List[ApiKeyResponse])
async def list_keys(
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    return await ApiKeyService.list_keys(db, org_id)


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    key_in: ApiKeyCreateRequest,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(require_role("owner", "admin"))
):
    res = await ApiKeyService.create_key(
        db, org_id, key_in.name,
        expires_at=key_in.expires_at,
        created_by_user_id=current_user.id,
    )
    from app.services.notification import NotificationService
    await NotificationService.create_notification(
        db,
        user_id=current_user.id,
        title="API Key Created",
        details=f'API key "{key_in.name}" was created.'
    )
    return res


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(require_role("owner", "admin"))
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.org_id == org_id)
    )
    db_key = result.scalar_one_or_none()
    key_name = db_key.name if db_key else "Unknown Key"

    await ApiKeyService.revoke_key(db, org_id, key_id)

    from app.services.notification import NotificationService
    await NotificationService.create_notification(
        db,
        user_id=current_user.id,
        title="API Key Revoked",
        details=f'API key "{key_name}" has been revoked.'
    )
    return None
