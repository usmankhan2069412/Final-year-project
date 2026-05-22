from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.organization import OrgMember, OrgRole
from app.models.user import User
from app.schemas.team import TeamMemberResponse
from app.services.billing import BillingService
from app.core.email import send_invite_email

class TeamService:
    @staticmethod
    def get_members(db: Session, org_id: uuid.UUID) -> List[TeamMemberResponse]:
        """Retrieve list of members in the organization."""
        memberships = (
            db.query(OrgMember)
            .options(joinedload(OrgMember.user))
            .filter(OrgMember.org_id == org_id)
            .all()
        )
        
        response = []
        for m in memberships:
            # Safe dereferencing of user relationship
            user = m.user
            if not user:
                continue
                
            response.append(
                TeamMemberResponse(
                    id=m.id,
                    user_id=m.user_id,
                    name=user.full_name,
                    email=user.email,
                    role=m.role.value if hasattr(m.role, "value") else str(m.role),
                    joined_at=datetime.now(timezone.utc),  # Fallback since created_at is not on OrgMember
                    avatar=None
                )
            )
        return response

    @staticmethod
    async def invite_member(db: Session, org_id: uuid.UUID, email: str, role: str) -> Optional[TeamMemberResponse]:
        """Invite a member by email. Directly add if they exist, send email if not."""
        # 1. Check if user is already a member
        existing_member = db.query(OrgMember).join(User).filter(
            OrgMember.org_id == org_id,
            User.email == email
        ).first()
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )

        # 2. Verify member quota
        if not BillingService.check_quota(db, org_id, "members"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Member limit exceeded. Please upgrade your subscription plan."
            )

        # 3. Look up user by email
        user = db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()

        if user:
            # Direct-add user to the organization
            db_role = OrgRole.ADMIN if role == "admin" else OrgRole.MEMBER
            membership = OrgMember(
                org_id=org_id,
                user_id=user.id,
                role=db_role
            )
            db.add(membership)
            db.commit()
            db.refresh(membership)

            return TeamMemberResponse(
                id=membership.id,
                user_id=user.id,
                name=user.full_name,
                email=user.email,
                role=membership.role.value if hasattr(membership.role, "value") else str(membership.role),
                joined_at=datetime.now(timezone.utc)
            )
        else:
            # User doesn't exist, send invitation email
            # Prepare invite link (normally points to frontend signup with query params)
            invite_link = f"http://localhost:5173/signup?invite_org={org_id}&email={email}"
            await send_invite_email(email_to=email, invite_link=invite_link)
            # Return None to signal that email invitation was sent
            return None

    @staticmethod
    def update_role(db: Session, org_id: uuid.UUID, member_id: uuid.UUID, role: str) -> TeamMemberResponse:
        """Update an organization member's role."""
        membership = db.query(OrgMember).filter(
            OrgMember.id == member_id,
            OrgMember.org_id == org_id
        ).first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization member not found"
            )

        # Owners cannot change their own roles or be changed through this endpoint
        if membership.role == OrgRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change role of the organization owner"
            )

        db_role = OrgRole.ADMIN if role == "admin" else OrgRole.MEMBER
        membership.role = db_role
        db.commit()
        db.refresh(membership)

        user = membership.user
        return TeamMemberResponse(
            id=membership.id,
            user_id=membership.user_id,
            name=user.full_name if user else None,
            email=user.email if user else "",
            role=membership.role.value if hasattr(membership.role, "value") else str(membership.role),
            joined_at=datetime.now(timezone.utc)
        )

    @staticmethod
    def remove_member(db: Session, org_id: uuid.UUID, member_id: uuid.UUID) -> bool:
        """Remove a member from the organization."""
        membership = db.query(OrgMember).filter(
            OrgMember.id == member_id,
            OrgMember.org_id == org_id
        ).first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization member not found"
            )

        if membership.role == OrgRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the organization owner"
            )

        db.delete(membership)
        db.commit()
        return True
