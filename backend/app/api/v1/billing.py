import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

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
async def get_plans(db: AsyncSession = Depends(get_tenant_db)):
    try:
        return await BillingService.get_plans(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription plans."
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        return await BillingService.get_subscription(db, org_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch current subscription details."
        )


@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe(
    request_in: SubscribeRequest,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(get_current_user)
):
    try:
        res = await BillingService.subscribe(db, org_id, request_in.plan_id)
        try:
            from app.services.notification import NotificationService
            await NotificationService.create_notification(
                db,
                user_id=current_user.id,
                title="Plan Upgraded",
                details=f"Successfully switched to the {res.plan.name} plan."
            )
        except Exception:
            # Notification delivery should not fail the subscription upgrade
            pass
        return res
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process subscription change."
        )


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user = Depends(get_current_user)
):
    try:
        res = await BillingService.cancel_subscription(db, org_id)
        try:
            from app.services.notification import NotificationService
            await NotificationService.create_notification(
                db,
                user_id=current_user.id,
                title="Plan Cancelled",
                details=f"Your subscription for the {res.plan.name} plan has been cancelled."
            )
        except Exception:
            # Notification delivery should not fail the cancellation
            pass
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription."
        )


@router.get("/history", response_model=List[BillingHistoryItem])
async def get_billing_history(
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        return await BillingService.get_billing_history(db, org_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch billing history."
        )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook(request: Request):
    return {"status": "success", "message": "Webhook received"}
