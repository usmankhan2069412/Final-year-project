from datetime import datetime, timedelta, timezone
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
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
    def get_plans(db: Session) -> List[SubscriptionPlan]:
        """List all subscription plans ordered by price."""
        return db.query(SubscriptionPlan).order_by(SubscriptionPlan.price_pkr).all()

    @staticmethod
    def get_subscription_usage(db: Session, org_id: uuid.UUID, period_start: datetime, period_end: datetime) -> SubscriptionUsage:
        """Compute live usage counts for bots, messages, and members."""
        # 1. Bots used (active chatbots, not deleted)
        bots_used = db.query(Chatbot).filter(
            Chatbot.org_id == org_id,
            Chatbot.deleted_at.is_(None)
        ).count()

        # 2. Messages used (messages in current billing cycle for this org's chatbots)
        messages_used = db.query(Message).join(
            Conversation, Message.conversation_id == Conversation.id
        ).join(
            Chatbot, Conversation.chatbot_id == Chatbot.id
        ).filter(
            Chatbot.org_id == org_id,
            Message.created_at >= period_start,
            Message.created_at <= period_end
        ).count()

        # 3. Members count
        members_count = db.query(OrgMember).filter(
            OrgMember.org_id == org_id
        ).count()

        return SubscriptionUsage(
            bots_used=bots_used,
            messages_used=messages_used,
            members_count=members_count
        )

    @staticmethod
    def get_subscription(db: Session, org_id: uuid.UUID) -> SubscriptionResponse:
        """Fetch the current subscription with live usage metrics."""
        # 1. Look for an active subscription first
        sub = db.query(Subscription).filter(
            Subscription.org_id == org_id,
            Subscription.status == "active"
        ).first()

        # 2. If no active subscription, check for the latest cancelled subscription
        if not sub:
            sub = db.query(Subscription).filter(
                Subscription.org_id == org_id,
                Subscription.status == "cancelled"
            ).order_by(Subscription.period_start.desc()).first()

        now = datetime.now(timezone.utc)
        is_expired = False
        if sub and sub.period_end:
            pe = sub.period_end
            if pe.tzinfo is None:
                pe = pe.replace(tzinfo=timezone.utc)
            is_expired = pe < now

        if not sub or is_expired:
            # Fallback/Safe state if no subscription is active (e.g. legacy orgs or expired)
            # Find Starter plan to show mock/default values
            starter_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == "Starter").first()
            if not starter_plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active subscription found and Starter plan is not seeded."
                )
            
            # Temporary mock active subscription response
            plan_resp = SubscriptionPlanResponse.model_validate(starter_plan)
            usage = SubscriptionUsage(bots_used=0, messages_used=0, members_count=1)
            try:
                usage = BillingService.get_subscription_usage(db, org_id, now, now + timedelta(days=30))
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
        usage = BillingService.get_subscription_usage(db, org_id, sub.period_start, sub.period_end)

        return SubscriptionResponse(
            id=sub.id,
            plan=plan_resp,
            status=sub.status,
            period_start=sub.period_start,
            period_end=sub.period_end,
            usage=usage
        )

    @staticmethod
    def subscribe(db: Session, org_id: uuid.UUID, plan_id: uuid.UUID) -> SubscriptionResponse:
        """Upgrade, downgrade, or update plan for an organization."""
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found"
            )

        # Cancel current active subscription(s)
        active_subs = db.query(Subscription).filter(
            Subscription.org_id == org_id,
            Subscription.status == "active"
        ).all()
        for sub in active_subs:
            sub.status = "cancelled"

        # Create new subscription
        now = datetime.now(timezone.utc)
        new_sub = Subscription(
            org_id=org_id,
            plan_id=plan.id,
            status="active",
            period_start=now,
            period_end=now + timedelta(days=30)
        )
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub)

        return BillingService.get_subscription(db, org_id)

    @staticmethod
    def cancel_subscription(db: Session, org_id: uuid.UUID) -> SubscriptionResponse:
        """Cancel active subscription (set status to 'cancelled')."""
        sub = db.query(Subscription).filter(
            Subscription.org_id == org_id,
            Subscription.status == "active"
        ).first()

        if not sub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found to cancel"
            )

        sub.status = "cancelled"
        db.commit()
        db.refresh(sub)

        return BillingService.get_subscription(db, org_id)

    @staticmethod
    def get_billing_history(db: Session, org_id: uuid.UUID) -> List[BillingHistoryItem]:
        """Retrieve billing history (mapping past/current subscriptions to history)."""
        subs = db.query(Subscription).filter(
            Subscription.org_id == org_id
        ).order_by(Subscription.period_start.desc()).all()

        history = []
        for s in subs:
            # Starter plan invoices show 0, others price_pkr
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
    def check_quota(db: Session, org_id: uuid.UUID, resource: str) -> bool:
        """Verify whether the organization is within its plan limits for a resource."""
        # 1. Look for an active subscription first
        sub = db.query(Subscription).filter(
            Subscription.org_id == org_id,
            Subscription.status == "active"
        ).first()

        # 2. If no active subscription, check for the latest cancelled subscription
        if not sub:
            sub = db.query(Subscription).filter(
                Subscription.org_id == org_id,
                Subscription.status == "cancelled"
            ).order_by(Subscription.period_start.desc()).first()

        now = datetime.now(timezone.utc)
        is_expired = False
        if sub and sub.period_end:
            pe = sub.period_end
            if pe.tzinfo is None:
                pe = pe.replace(tzinfo=timezone.utc)
            is_expired = pe < now

        plan = sub.plan if (sub and not is_expired) else None
        if not plan:
            # Fallback to Starter plan limit
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == "Starter").first()
            if not plan:
                return True # If Starter plan is missing, don't block in dev

        # Retrieve usage counts
        if resource == "bots":
            if plan.max_bots is None:
                return True
            current_bots = db.query(Chatbot).filter(
                Chatbot.org_id == org_id,
                Chatbot.deleted_at.is_(None)
            ).count()
            return current_bots < plan.max_bots

        elif resource == "messages":
            if plan.max_messages_per_month is None:
                return True
            
            period_start = sub.period_start if (sub and not is_expired) else now - timedelta(days=30)
            period_end = sub.period_end if (sub and not is_expired) else now
            
            current_messages = db.query(Message).join(
                Conversation, Message.conversation_id == Conversation.id
            ).join(
                Chatbot, Conversation.chatbot_id == Chatbot.id
            ).filter(
                Chatbot.org_id == org_id,
                Message.created_at >= period_start,
                Message.created_at <= period_end
            ).count()
            return current_messages < plan.max_messages_per_month

        elif resource == "members":
            if plan.max_members is None:
                return True
            current_members = db.query(OrgMember).filter(
                OrgMember.org_id == org_id
            ).count()
            return current_members < plan.max_members

        return True


class QuotaGuard:
    @staticmethod
    def check_quota(db: Session, org_id: uuid.UUID, resource: str) -> bool:
        """Helper to enforce quotas."""
        return BillingService.check_quota(db, org_id, resource)
