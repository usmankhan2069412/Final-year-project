from datetime import datetime, timedelta, timezone
import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.subscription import SubscriptionPlan, Subscription
from app.models.chatbot import Chatbot
from app.models.conversation import Conversation, Message
from app.models.organization import OrgMember
from app.schemas.billing import (
    SubscriptionPlanResponse,
    SubscriptionResponse,
    SubscriptionUsage,
    BillingHistoryItem
)


class BillingService:
    @staticmethod
    async def get_plans(db: AsyncSession) -> List[SubscriptionPlan]:
        result = await db.execute(
            select(SubscriptionPlan).order_by(SubscriptionPlan.price_pkr)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_subscription_usage(db: AsyncSession, org_id: uuid.UUID, period_start: datetime, period_end: datetime) -> SubscriptionUsage:
        result = await db.execute(
            select(func.count(Chatbot.id)).where(
                Chatbot.org_id == org_id,
                Chatbot.deleted_at.is_(None)
            )
        )
        bots_used = result.scalar() or 0

        subq = select(Conversation.id).join(Chatbot, Conversation.chatbot_id == Chatbot.id).where(
            Chatbot.org_id == org_id
        ).subquery()
        result = await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id.in_(select(subq.c.id)),
                Message.created_at >= period_start,
                Message.created_at <= period_end
            )
        )
        messages_used = result.scalar() or 0

        result = await db.execute(
            select(func.count(OrgMember.id)).where(OrgMember.org_id == org_id)
        )
        members_count = result.scalar() or 0

        return SubscriptionUsage(
            bots_used=bots_used,
            messages_used=messages_used,
            members_count=members_count
        )

    @staticmethod
    async def get_subscription(db: AsyncSession, org_id: uuid.UUID) -> SubscriptionResponse:
        result = await db.execute(
            select(Subscription).where(
                Subscription.org_id == org_id,
                Subscription.status == "active"
            )
        )
        sub = result.scalar_one_or_none()

        if not sub:
            result = await db.execute(
                select(Subscription).where(
                    Subscription.org_id == org_id,
                    Subscription.status == "cancelled"
                ).order_by(Subscription.period_start.desc())
            )
            sub = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        is_expired = False
        if sub and sub.period_end:
            pe = sub.period_end
            if pe.tzinfo is None:
                pe = pe.replace(tzinfo=timezone.utc)
            is_expired = pe < now

        if not sub or is_expired:
            result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.name == "Starter")
            )
            starter_plan = result.scalar_one_or_none()
            if not starter_plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active subscription found and Starter plan is not seeded."
                )

            plan_resp = SubscriptionPlanResponse.model_validate(starter_plan)
            usage = SubscriptionUsage(bots_used=0, messages_used=0, members_count=1)
            try:
                usage = await BillingService.get_subscription_usage(db, org_id, now, now + timedelta(days=30))
            except Exception:
                pass
            return SubscriptionResponse(
                id=uuid.uuid4(),
                plan=plan_resp,
                status="active",
                period_start=now,
                period_end=now + timedelta(days=30),
                usage=usage
            )

        plan_resp = SubscriptionPlanResponse.model_validate(sub.plan)
        usage = await BillingService.get_subscription_usage(db, org_id, sub.period_start, sub.period_end)

        return SubscriptionResponse(
            id=sub.id,
            plan=plan_resp,
            status=sub.status,
            period_start=sub.period_start,
            period_end=sub.period_end,
            usage=usage
        )

    @staticmethod
    async def subscribe(db: AsyncSession, org_id: uuid.UUID, plan_id: uuid.UUID) -> SubscriptionResponse:
        result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found"
            )

        result = await db.execute(
            select(Subscription).where(
                Subscription.org_id == org_id,
                Subscription.status == "active"
            )
        )
        active_subs = list(result.scalars().all())
        for sub in active_subs:
            sub.status = "cancelled"

        now = datetime.now(timezone.utc)
        new_sub = Subscription(
            org_id=org_id,
            plan_id=plan.id,
            status="active",
            period_start=now,
            period_end=now + timedelta(days=30)
        )
        db.add(new_sub)
        await db.commit()
        await db.refresh(new_sub)

        return await BillingService.get_subscription(db, org_id)

    @staticmethod
    async def cancel_subscription(db: AsyncSession, org_id: uuid.UUID) -> SubscriptionResponse:
        result = await db.execute(
            select(Subscription).where(
                Subscription.org_id == org_id,
                Subscription.status == "active"
            )
        )
        sub = result.scalar_one_or_none()

        if not sub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found to cancel"
            )

        sub.status = "cancelled"
        await db.commit()
        await db.refresh(sub)

        return await BillingService.get_subscription(db, org_id)

    @staticmethod
    async def get_billing_history(db: AsyncSession, org_id: uuid.UUID) -> List[BillingHistoryItem]:
        result = await db.execute(
            select(Subscription)
            .where(Subscription.org_id == org_id)
            .order_by(Subscription.period_start.desc())
        )
        subs = list(result.scalars().all())

        history = []
        for s in subs:
            history.append(
                BillingHistoryItem(
                    id=s.id,
                    date=s.created_at,
                    amount=float(s.plan.price_pkr),
                    status="Paid" if s.status in ["active", "cancelled"] else "Failed",
                    invoice=f"INV-{s.created_at.strftime('%Y%m%d')}-{str(s.id)[:8].upper()}"
                )
            )
        return history

    @staticmethod
    async def check_quota(db: AsyncSession, org_id: uuid.UUID, resource: str) -> bool:
        result = await db.execute(
            select(Subscription).where(
                Subscription.org_id == org_id,
                Subscription.status == "active"
            )
        )
        sub = result.scalar_one_or_none()

        if not sub:
            result = await db.execute(
                select(Subscription).where(
                    Subscription.org_id == org_id,
                    Subscription.status == "cancelled"
                ).order_by(Subscription.period_start.desc())
            )
            sub = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        is_expired = False
        if sub and sub.period_end:
            pe = sub.period_end
            if pe.tzinfo is None:
                pe = pe.replace(tzinfo=timezone.utc)
            is_expired = pe < now

        plan = sub.plan if (sub and not is_expired) else None
        if not plan:
            result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.name == "Starter")
            )
            plan = result.scalar_one_or_none()
            if not plan:
                return True

        if resource == "bots":
            if plan.max_bots is None:
                return True
            result = await db.execute(
                select(func.count(Chatbot.id)).where(
                    Chatbot.org_id == org_id,
                    Chatbot.deleted_at.is_(None)
                )
            )
            current_bots = result.scalar() or 0
            return current_bots < plan.max_bots

        elif resource == "messages":
            if plan.max_messages_per_month is None:
                return True

            period_start = sub.period_start if (sub and not is_expired) else now - timedelta(days=30)
            period_end = sub.period_end if (sub and not is_expired) else now

            subq = select(Conversation.id).join(Chatbot, Conversation.chatbot_id == Chatbot.id).where(
                Chatbot.org_id == org_id
            ).subquery()
            result = await db.execute(
                select(func.count(Message.id)).where(
                    Message.conversation_id.in_(select(subq.c.id)),
                    Message.created_at >= period_start,
                    Message.created_at <= period_end
                )
            )
            current_messages = result.scalar() or 0
            return current_messages < plan.max_messages_per_month

        elif resource == "members":
            if plan.max_members is None:
                return True
            result = await db.execute(
                select(func.count(OrgMember.id)).where(OrgMember.org_id == org_id)
            )
            current_members = result.scalar() or 0
            return current_members < plan.max_members

        return True


class QuotaGuard:
    @staticmethod
    async def check_quota(db: AsyncSession, org_id: uuid.UUID, resource: str) -> bool:
        return await BillingService.check_quota(db, org_id, resource)
