from typing import Generator, Optional
import uuid
from fastapi import Depends, HTTPException, status, Header, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.organization import OrgMember

reusable_oauth2 = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    token_credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
) -> User:
    """
    Extract + decode the JWT credentials and return the active User.
    Raises HTTP 401 for any invalid/expired token or missing user.
    """
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

    user = db.query(User).filter(
        User.id == user_uuid,
        User.deleted_at == None,  # noqa: E711
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def update_api_key_last_used(key_hash: str):
    """Updates the last_used_at timestamp on the API key using a dedicated session."""
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


def get_current_user_or_api_key(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> User:
    """
    Authenticate using either JWT (Authorization: Bearer) or API Key (X-API-Key).
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        import hashlib
        from datetime import datetime, timezone
        from app.models.api_key import ApiKey
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        api_key_record = db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None)
        ).first()
        
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
            
        db.execute(
            text("SELECT set_config('app.current_org_id', :org_id, true)"),
            {"org_id": str(api_key_record.org_id)}
        )
        
        owner = db.query(User).filter(User.id == api_key_record.created_by_user_id).first()
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with API key not found"
            )
        return owner

    # Fallback to JWT Authorization Header
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

    user = db.query(User).filter(
        User.id == user_uuid,
        User.deleted_at == None,
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def resolve_tenant_org_member(
    db: Session,
    current_user: User,
    x_org_id: Optional[str] = None,
    api_key_org_id: Optional[uuid.UUID] = None,
) -> OrgMember:
    """
    Resolve the active organization membership for the user.
    """
    if api_key_org_id:
        membership = db.query(OrgMember).filter(
            OrgMember.user_id == current_user.id,
            OrgMember.org_id == api_key_org_id,
        ).first()
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

        membership = db.query(OrgMember).filter(
            OrgMember.user_id == current_user.id,
            OrgMember.org_id == org_uuid,
        ).first()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to the requested organization is denied",
            )
        return membership
    else:
        # Fallback: use the user's first (oldest) organization
        membership = db.query(OrgMember).filter(
            OrgMember.user_id == current_user.id,
        ).first()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to any organization",
            )
        return membership


def get_org_id(db: Session) -> uuid.UUID:
    """Helper to retrieve the resolved organization ID from the db session context."""
    org_id_str = db.execute(text("SELECT current_setting('app.current_org_id', true)")).scalar()
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


def get_tenant_member(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
    x_org_id: Optional[str] = Header(None, alias="X-Org-ID"),
) -> OrgMember:
    """Dependency that resolves the active organization membership."""
    api_key_org_id = getattr(request.state, "api_key_org_id", None)
    return resolve_tenant_org_member(db, current_user, x_org_id, api_key_org_id)


def get_current_org_id(
    membership: OrgMember = Depends(get_tenant_member),
) -> uuid.UUID:
    """Dependency that returns the current organization ID."""
    return membership.org_id


def get_tenant_db(
    db: Session = Depends(get_db),
    membership: OrgMember = Depends(get_tenant_member),
) -> Generator[Session, None, None]:
    """
    Resolve the active organization for the request and bind it to the
    PostgreSQL session via set_config('app.current_org_id', ...) so that
    all subsequent queries run under RLS isolation for that tenant.
    """
    # Bind tenant context for RLS — transaction-local only (is_local=true)
    db.execute(
        text("SELECT set_config('app.current_org_id', :org_id, true)"),
        {"org_id": str(membership.org_id)},
    )

    yield db
    # Session cleanup is handled by get_db's finally block


def require_role(*allowed_roles: str):
    """
    Dependency that checks the current user has one of the allowed roles
    in the active organization (resolved from X-Org-ID or fallback).
    """
    def _check(
        db: Session = Depends(get_db),
        membership: OrgMember = Depends(get_tenant_member),
    ) -> User:
        role_str = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
        if role_str not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        db.execute(
            text("SELECT set_config('app.current_org_id', :org_id, true)"),
            {"org_id": str(membership.org_id)},
        )
        
        user = membership.user
        if not user:
            # Fallback lookup in case relationship is not loaded
            user = db.query(User).filter(User.id == membership.user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User associated with membership not found."
                )
        return user
    return _check


# API Key and JWT Authentication utilities moved to the top of the file.
