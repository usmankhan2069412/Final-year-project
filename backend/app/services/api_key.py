import secrets
import hashlib
from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyResponse, ApiKeyCreateResponse


class ApiKeyService:
    @staticmethod
    async def list_keys(db: AsyncSession, org_id: uuid.UUID) -> List[ApiKeyResponse]:
        result = await db.execute(
            select(ApiKey)
            .where(ApiKey.org_id == org_id)
            .order_by(ApiKey.created_at.desc())
        )
        keys = list(result.scalars().all())

        now = datetime.now(timezone.utc)
        response = []
        for k in keys:
            if k.revoked_at is not None:
                status_str = "revoked"
            elif k.expires_at is not None and k.expires_at <= now:
                status_str = "expired"
            else:
                status_str = "active"
            response.append(
                ApiKeyResponse(
                    id=k.id,
                    name=k.name,
                    prefix=k.key_prefix,
                    created_at=k.created_at,
                    last_used=k.last_used_at,
                    expires_at=k.expires_at,
                    status=status_str
                )
            )
        return response

    @staticmethod
    async def create_key(
        db: AsyncSession,
        org_id: uuid.UUID,
        name: str,
        expires_at: Optional[datetime] = None,
        created_by_user_id: Optional[uuid.UUID] = None,
    ) -> ApiKeyCreateResponse:
        token = secrets.token_urlsafe(32)
        raw_key = f"ak_prod_{token}"

        prefix = f"ak_prod_{token[:6]}..."

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        db_key = ApiKey(
            org_id=org_id,
            created_by_user_id=created_by_user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=prefix,
            expires_at=expires_at,
        )
        db.add(db_key)
        await db.commit()
        await db.refresh(db_key)

        return ApiKeyCreateResponse(
            id=db_key.id,
            name=db_key.name,
            key=raw_key,
            prefix=prefix,
            created_at=db_key.created_at,
            expires_at=db_key.expires_at,
        )

    @staticmethod
    async def revoke_key(db: AsyncSession, org_id: uuid.UUID, key_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.org_id == org_id
            )
        )
        db_key = result.scalar_one_or_none()

        if not db_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API Key not found or access denied"
            )

        if db_key.revoked_at is None:
            db_key.revoked_at = datetime.now(timezone.utc)
            await db.commit()

        return True
