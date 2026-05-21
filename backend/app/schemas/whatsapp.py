import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.conversation import Channel

# --- Webhook Models ---
class WebhookVerifyParams(BaseModel):
    """Query params for GET /channels/whatsapp/webhook"""
    hub_mode: str
    hub_verify_token: str
    hub_challenge: str


class WhatsAppMessage(BaseModel):
    """Parsed inbound message from Meta's nested payload"""
    message_id: str
    sender_phone: str
    text: str
    timestamp: str


# --- Deployment CRUD Models ---
class DeploymentCreate(BaseModel):
    chatbot_id: uuid.UUID
    channel: Channel = Channel.WEB
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None


class DeploymentResponse(BaseModel):
    id: uuid.UUID
    chatbot_id: uuid.UUID
    channel: Channel
    is_active: bool
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    webhook_verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DeploymentStatusUpdate(BaseModel):
    is_active: bool
