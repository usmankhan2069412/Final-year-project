from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.organization import OrgMember, OrgRole
from app.models.user import User
from app.schemas.team import TeamMemberResponse
from app.services.billing import BillingService
from app.core.email import send_invite_email


class TeamService:
    @staticmethod
    async def get_members(db: AsyncSession, org_id: uuid.UUID) -> List[TeamMemberResponse]:
        from sqlalchemy.orm import joinedload
        stmt = (
            select(OrgMember)
            .options(joinedload(OrgMember.user))
            .where(OrgMember.org_id == org_id)
        )
        result = await db.execute(stmt)
        memberships = list(result.scalars().all())

        response = []
        for m in memberships:
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
                    joined_at=datetime.now(timezone.utc),
                    avatar=None
                )
            )
        return response

    @staticmethod
    async def invite_member(db: AsyncSession, org_id: uuid.UUID, email: str, role: str) -> Optional[TeamMemberResponse]:
        result = await db.execute(
            select(OrgMember)
            .join(User, OrgMember.user_id == User.id)
            .where(OrgMember.org_id == org_id, User.email == email)
        )
        existing_member = result.scalar_one_or_none()
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )

        if not await BillingService.check_quota(db, org_id, "members"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Member limit exceeded. Please upgrade your subscription plan."
            )

        result = await db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()

        if user:
            db_role = OrgRole.ADMIN if role == "admin" else OrgRole.MEMBER
            membership = OrgMember(
                org_id=org_id,
                user_id=user.id,
                role=db_role
            )
            db.add(membership)
            await db.commit()
            await db.refresh(membership)

            return TeamMemberResponse(
                id=membership.id,
                user_id=user.id,
                name=user.full_name,
                email=user.email,
                role=membership.role.value if hasattr(membership.role, "value") else str(membership.role),
                joined_at=datetime.now(timezone.utc)
            )
        else:
            invite_link = f"http://localhost:5173/signup?invite_org={org_id}&email={email}"
            await send_invite_email(email_to=email, invite_link=invite_link)
            return None

    @staticmethod
    async def update_role(db: AsyncSession, org_id: uuid.UUID, member_id: uuid.UUID, role: str) -> TeamMemberResponse:
        result = await db.execute(
            select(OrgMember).where(
                OrgMember.id == member_id,
                OrgMember.org_id == org_id
            )
        )
        membership = result.scalar_one_or_none()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization member not found"
            )

        if membership.role == OrgRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change role of the organization owner"
            )

        db_role = OrgRole.ADMIN if role == "admin" else OrgRole.MEMBER
        membership.role = db_role
        await db.commit()
        await db.refresh(membership)

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
    async def remove_member(db: AsyncSession, org_id: uuid.UUID, member_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(OrgMember).where(
                OrgMember.id == member_id,
                OrgMember.org_id == org_id
            )
        )
        membership = result.scalar_one_or_none()

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

        await db.delete(membership)
        await db.commit()
        return True
