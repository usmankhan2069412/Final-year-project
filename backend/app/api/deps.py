from typing import Generator, Optional
import uuid
from fastapi import Depends, HTTPException, status, Header
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
    Extract + decode the Bearer JWT and return the active User.
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


def get_tenant_db(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_org_id: Optional[str] = Header(None, alias="X-Org-ID"),
) -> Generator[Session, None, None]:
    """
    Resolve the active organization for the request and bind it to the
    PostgreSQL session via set_config('app.current_org_id', ...) so that
    all subsequent queries run under RLS isolation for that tenant.
    """
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
        resolved_org_id = org_uuid
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
        resolved_org_id = membership.org_id

    # Bind tenant context for RLS — transaction-local only (is_local=true)
    db.execute(
        text("SELECT set_config('app.current_org_id', :org_id, true)"),
        {"org_id": str(resolved_org_id)},
    )

    yield db
    # Session cleanup is handled by get_db's finally block
