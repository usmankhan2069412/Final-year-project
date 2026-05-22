import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db, get_current_org_id
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
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Subscribe or change plans for the active organization."""
    return BillingService.subscribe(db, org_id, request_in.plan_id)


@router.post("/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Cancel the active subscription (turns status to 'cancelled')."""
    return BillingService.cancel_subscription(db, org_id)


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
