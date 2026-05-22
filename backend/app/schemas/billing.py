import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class SubscriptionPlanResponse(BaseModel):
    id: uuid.UUID
    name: str
    price_pkr: float
    max_bots: Optional[int] = None      # None = unlimited
    max_messages_per_month: Optional[int] = None
    max_members: Optional[int] = None
    features: List[str]
    is_popular: bool

    model_config = ConfigDict(from_attributes=True)

class SubscriptionUsage(BaseModel):
    bots_used: int
    messages_used: int
    members_count: int

    model_config = ConfigDict(from_attributes=True)

class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    plan: SubscriptionPlanResponse
    status: str                    # 'active', 'cancelled', 'past_due', 'trialing'
    period_start: datetime
    period_end: datetime
    usage: SubscriptionUsage       # current bots, messages, members counts

    model_config = ConfigDict(from_attributes=True)

class SubscribeRequest(BaseModel):
    plan_id: uuid.UUID

class BillingHistoryItem(BaseModel):
    id: uuid.UUID
    date: datetime
    amount: float
    status: str
    invoice: str

    model_config = ConfigDict(from_attributes=True)
