from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_tenant_db
from app.models.user import User
from app.models.organization import Organization, OrgMember
from app.schemas.auth import (
    UserMeResponse,
    UserResponse,
    OrgResponse,
    UserUpdateRequest,
    PasswordUpdateRequest,
)
from app.services.auth import generate_slug
from app.core.security import verify_password, get_password_hash

router = APIRouter()


@router.get("/me", response_model=UserMeResponse)
async def get_user_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db)
):
    result = await db.execute(select(OrgMember).where(OrgMember.user_id == current_user.id))
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    result = await db.execute(select(Organization).where(Organization.id == membership.org_id))
    active_org = result.scalar_one_or_none()
    if not active_org:
        raise HTTPException(status_code=404, detail="Active organization not found")

    return UserMeResponse(
        user=UserResponse.model_validate(current_user),
        active_organization=OrgResponse.model_validate(active_org)
    )


@router.put("/me", response_model=UserMeResponse)
async def update_user_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db)
):
    if payload.email is not None:
        new_email = payload.email.strip().lower()
        if new_email != current_user.email:
            result = await db.execute(
                select(User).where(User.email == new_email, User.deleted_at == None)
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already registered")
            current_user.email = new_email

    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()

    result = await db.execute(select(OrgMember).where(OrgMember.user_id == current_user.id))
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    result = await db.execute(select(Organization).where(Organization.id == membership.org_id))
    active_org = result.scalar_one_or_none()
    if not active_org:
        raise HTTPException(status_code=404, detail="Active organization not found")

    if payload.org_slug is not None:
        clean_slug = generate_slug(payload.org_slug)
        if not clean_slug:
            raise HTTPException(status_code=400, detail="Invalid organization slug format")
        if clean_slug != active_org.slug:
            result = await db.execute(select(Organization).where(Organization.slug == clean_slug))
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Organization slug already in use")
            active_org.slug = clean_slug

    await db.commit()
    await db.refresh(current_user)
    await db.refresh(active_org)

    from app.services.notification import NotificationService
    await NotificationService.create_notification(
        db,
        user_id=current_user.id,
        title="Profile Updated",
        details="Your profile details have been saved successfully."
    )

    return UserMeResponse(
        user=UserResponse.model_validate(current_user),
        active_organization=OrgResponse.model_validate(active_org)
    )


@router.put("/me/password")
async def update_user_password(
    payload: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db)
):
    if current_user.password_hash:
        if not verify_password(payload.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect current password")

    current_user.password_hash = get_password_hash(payload.new_password)
    await db.commit()

    from app.services.notification import NotificationService
    await NotificationService.create_notification(
        db,
        user_id=current_user.id,
        title="Password Updated",
        details="Your password was changed successfully."
    )

    return {"status": "success", "message": "Password updated successfully"}
