import logging
from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.services.whatsapp import WhatsAppService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/whatsapp/webhook", response_class=PlainTextResponse)
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Meta webhook subscription verification challenge handshake.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully.")
        return hub_challenge
        
    logger.warning("WhatsApp webhook verification handshake failed.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch or invalid mode"
    )


@router.post("/whatsapp/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Receive webhook notifications from Meta.
    Verifies payload signature and processes message asynchronously.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    if not WhatsAppService.verify_webhook_signature(raw_body, signature):
        logger.warning("WhatsApp webhook event rejected: invalid signature")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature"
        )
        
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
        
    # Queue processing to a background task so we can return a 200 OK response immediately
    background_tasks.add_task(WhatsAppService.process_inbound_message, db, payload)
    
    return {"status": "received"}
