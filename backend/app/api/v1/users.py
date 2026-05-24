from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
def get_user_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Retrieve the current user profile along with their active organization.
    The database session 'db' is automatically initialized and isolated under PostgreSQL RLS.
    """
    # Fetch active organization resolved for the current tenant context
    membership = db.query(OrgMember).filter(OrgMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    active_org = db.query(Organization).filter(Organization.id == membership.org_id).first()
    if not active_org:
        raise HTTPException(status_code=404, detail="Active organization not found")
    
    return UserMeResponse(
        user=UserResponse.model_validate(current_user),
        active_organization=OrgResponse.model_validate(active_org)
    )

@router.put("/me", response_model=UserMeResponse)
def update_user_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Update the current user profile (full name, email) and active organization slug.
    Checks for email and org_slug uniqueness before updating.
    """
    # 1. Update user email if changed, verifying uniqueness
    if payload.email is not None:
        new_email = payload.email.strip().lower()
        if new_email != current_user.email:
            existing = db.query(User).filter(User.email == new_email, User.deleted_at == None).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")
            current_user.email = new_email

    # 2. Update full name if provided
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()

    # 3. Update active organization slug if provided, generating slug & verifying uniqueness
    membership = db.query(OrgMember).filter(OrgMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    active_org = db.query(Organization).filter(Organization.id == membership.org_id).first()
    if not active_org:
        raise HTTPException(status_code=404, detail="Active organization not found")

    if payload.org_slug is not None:
        clean_slug = generate_slug(payload.org_slug)
        if not clean_slug:
            raise HTTPException(status_code=400, detail="Invalid organization slug format")
        if clean_slug != active_org.slug:
            existing_org = db.query(Organization).filter(Organization.slug == clean_slug).first()
            if existing_org:
                raise HTTPException(status_code=400, detail="Organization slug already in use")
            active_org.slug = clean_slug

    db.commit()
    db.refresh(current_user)
    db.refresh(active_org)

    # Save notification to DB
    from app.services.notification import NotificationService
    NotificationService.create_notification(
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
def update_user_password(
    payload: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Update the current user password after verifying their current password.
    """
    if current_user.password_hash:
        if not verify_password(payload.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect current password")
    
    current_user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    
    # Save notification to DB
    from app.services.notification import NotificationService
    NotificationService.create_notification(
        db,
        user_id=current_user.id,
        title="Password Updated",
        details="Your password was changed successfully."
    )

    return {"status": "success", "message": "Password updated successfully"}

