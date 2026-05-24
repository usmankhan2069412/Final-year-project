import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db, get_current_org_id, get_current_user
from app.services.billing import BillingService
from app.schemas.billing import (
    SubscriptionPlanResponse,
    SubscriptionResponse,
    SubscribeRequest,
    BillingHistoryItem
)

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
def get_plans(db: Session = Depends(get_tenant_db)):
    """List all available subscription plans."""
    return BillingService.get_plans(db)


@router.get("/subscription", response_model=SubscriptionResponse)
def get_subscription(
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Get the current organization's active subscription and usage."""
    return BillingService.get_subscription(db, org_id)


@router.post("/subscribe", response_model=SubscriptionResponse)
def subscribe(
    request_in: SubscribeRequest,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(get_current_user)
):
    """Subscribe or change plans for the active organization."""
    res = BillingService.subscribe(db, org_id, request_in.plan_id)
    from app.services.notification import NotificationService
    NotificationService.create_notification(
        db,
        user_id=current_user.id,
        title="Plan Upgraded",
        details=f"Successfully switched to the {res.plan.name} plan."
    )
    return res


@router.post("/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(get_current_user)
):
    """Cancel the active subscription (turns status to 'cancelled')."""
    res = BillingService.cancel_subscription(db, org_id)
    from app.services.notification import NotificationService
    NotificationService.create_notification(
        db,
        user_id=current_user.id,
        title="Plan Cancelled",
        details=f"Your subscription for the {res.plan.name} plan has been cancelled."
    )
    return res


@router.get("/history", response_model=List[BillingHistoryItem])
def get_billing_history(
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Get the billing history for the active organization."""
    return BillingService.get_billing_history(db, org_id)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook(request: Request):
    """Stub endpoint for payment gateway webhooks."""
    # Webhook signature validation and handling can be implemented here.
    # Currently returning a placeholder dictionary for the MVP.
    return {"status": "success", "message": "Webhook received"}
