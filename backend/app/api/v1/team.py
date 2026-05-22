import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db, require_role, get_current_org_id
from app.services.team import TeamService
from app.schemas.team import (
    TeamMemberResponse,
    InviteMemberRequest,
    UpdateRoleRequest
)

router = APIRouter(prefix="/settings/team", tags=["Team Settings"])


@router.get("", response_model=List[TeamMemberResponse])
def get_members(
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """List all organization members."""
    return TeamService.get_members(db, org_id)


@router.post("/invite", response_model=Optional[TeamMemberResponse])
async def invite_member(
    invite_in: InviteMemberRequest,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(require_role("owner", "admin"))
):
    """Invite a member or add directly if they exist. Requires owner or admin role."""
    return await TeamService.invite_member(db, org_id, invite_in.email, invite_in.role)


@router.put("/{member_id}/role", response_model=TeamMemberResponse)
def update_role(
    member_id: uuid.UUID,
    role_in: UpdateRoleRequest,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(require_role("owner"))
):
    """Update a member's role. Requires owner role."""
    return TeamService.update_role(db, org_id, member_id, role_in.role)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    member_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(require_role("owner", "admin"))
):
    """Remove a member from the organization. Requires owner or admin role."""
    TeamService.remove_member(db, org_id, member_id)
    return None
