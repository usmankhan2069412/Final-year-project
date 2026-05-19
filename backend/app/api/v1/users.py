from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_tenant_db
from app.models.user import User
from app.models.organization import Organization, OrgMember
from app.schemas.auth import UserMeResponse, UserResponse, OrgResponse

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
    active_org = db.query(Organization).filter(Organization.id == membership.org_id).first()
    
    return UserMeResponse(
        user=UserResponse.model_validate(current_user),
        active_organization=OrgResponse.model_validate(active_org)
    )
