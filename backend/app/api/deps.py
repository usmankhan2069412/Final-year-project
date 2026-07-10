from typing import AsyncGenerator, Optional
import uuid
from fastapi import Depends, HTTPException, status, Header, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.organization import OrgMember

reusable_oauth2 = HTTPBearer()


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token_credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
) -> User:
    user_id_str = decode_access_token(token_credentials.credentials)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.id == user_uuid, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def update_api_key_last_used(key_hash: str):
    """Updates the last_used_at timestamp on the API key using a dedicated sync session."""
    from app.db.session import SessionLocal
    from app.models.api_key import ApiKey
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        api_key_record = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
        if api_key_record:
            api_key_record.last_used_at = datetime.now(timezone.utc)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


async def get_current_user_or_api_key(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> User:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        import hashlib
        from datetime import datetime, timezone
        from app.models.api_key import ApiKey

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.key_hash == key_hash,
                ApiKey.revoked_at.is_(None)
            )
        )
        api_key_record = result.scalar_one_or_none()

        if not api_key_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked API key"
            )

        if api_key_record.expires_at is not None:
            expires_at = api_key_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Expired API key"
                )

        background_tasks.add_task(update_api_key_last_used, key_hash)
        request.state.api_key_org_id = api_key_record.org_id
        request.state.authenticated_with_api_key = True

        await db.execute(
            text("SELECT set_config('app.current_org_id', :org_id, true)"),
            {"org_id": str(api_key_record.org_id)}
        )

        result = await db.execute(select(User).where(User.id == api_key_record.created_by_user_id))
        owner = result.scalar_one_or_none()
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with API key not found"
            )
        return owner

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ", 1)[1]
    user_id_str = decode_access_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.id == user_uuid, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def resolve_tenant_org_member(
    db: AsyncSession,
    current_user: User,
    x_org_id: Optional[str] = None,
    api_key_org_id: Optional[uuid.UUID] = None,
) -> OrgMember:
    if api_key_org_id:
        result = await db.execute(
            select(OrgMember).where(
                OrgMember.user_id == current_user.id,
                OrgMember.org_id == api_key_org_id,
            )
        )
        membership = result.scalar_one_or_none()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key organization is not accessible to this user",
            )
        return membership

    if x_org_id:
        try:
            org_uuid = uuid.UUID(x_org_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Org-ID header format",
            )

        result = await db.execute(
            select(OrgMember).where(
                OrgMember.user_id == current_user.id,
                OrgMember.org_id == org_uuid,
            )
        )
        membership = result.scalar_one_or_none()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to the requested organization is denied",
            )
        return membership
    else:
        result = await db.execute(
            select(OrgMember).where(OrgMember.user_id == current_user.id)
        )
        membership = result.scalar_one_or_none()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to any organization",
            )
        return membership


async def get_org_id(db: AsyncSession) -> uuid.UUID:
    result = await db.execute(text("SELECT current_setting('app.current_org_id', true)"))
    org_id_str = result.scalar()
    if not org_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is missing."
        )
    try:
        return uuid.UUID(org_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format in tenant context."
        )


async def get_tenant_member(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
    x_org_id: Optional[str] = Header(None, alias="X-Org-ID"),
) -> OrgMember:
    api_key_org_id = getattr(request.state, "api_key_org_id", None)
    return await resolve_tenant_org_member(db, current_user, x_org_id, api_key_org_id)


async def get_current_org_id(
    membership: OrgMember = Depends(get_tenant_member),
) -> uuid.UUID:
    return membership.org_id


async def get_tenant_db(
    db: AsyncSession = Depends(get_db),
    membership: OrgMember = Depends(get_tenant_member),
) -> AsyncGenerator[AsyncSession, None]:
    await db.execute(
        text("SELECT set_config('app.current_org_id', :org_id, true)"),
        {"org_id": str(membership.org_id)},
    )

    yield db


def require_role(*allowed_roles: str):
    async def _check(
        db: AsyncSession = Depends(get_db),
        membership: OrgMember = Depends(get_tenant_member),
    ) -> User:
        role_str = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
        if role_str not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        await db.execute(
            text("SELECT set_config('app.current_org_id', :org_id, true)"),
            {"org_id": str(membership.org_id)},
        )

        user = membership.user
        if not user:
            result = await db.execute(select(User).where(User.id == membership.user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User associated with membership not found."
                )
        return user
    return _check
