import hmac
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation, ConversationStatus, Deployment, ProcessedEvent
from app.models.chatbot import Chatbot
from app.services.chat import ChatService
from app.schemas.whatsapp import WhatsAppMessage
from app.services.outbox import OutboxService

logger = logging.getLogger(__name__)

class WhatsAppService:
    @staticmethod
    def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
        """
        Verify that the payload was sent by Meta using the X-Hub-Signature-256.
        """
        if not settings.WHATSAPP_APP_SECRET:
            logger.warning("WHATSAPP_APP_SECRET not configured, bypassing signature check (development only)")
            return True
            
        if not signature:
            return False
            
        if signature.startswith("sha256="):
            signature = signature[7:]
            
        expected_signature = hmac.new(
            settings.WHATSAPP_APP_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

    @staticmethod
    def parse_incoming_message(payload: dict) -> Optional[WhatsAppMessage]:
        """
        Parse incoming text message metadata and content from Meta's payload.
        Returns None if payload is not a text message event.
        """
        try:
            entry = payload.get("entry", [])[0]
            change = entry.get("changes", [])[0]
            value = change.get("value", {})
            
            # We only process 'messages' changes
            if change.get("field") != "messages":
                return None
                
            messages = value.get("messages", [])
            if not messages:
                return None
                
            msg = messages[0]
            # Ignore message read/delivery status updates, only process inbound text messages
            if msg.get("type") != "text":
                return None
                
            contacts = value.get("contacts", [])
            sender_phone = msg.get("from")
            if not sender_phone and contacts:
                sender_phone = contacts[0].get("wa_id")
                
            body = msg.get("text", {}).get("body", "")
            
            if not sender_phone or not body:
                return None
                
            return WhatsAppMessage(
                message_id=msg.get("id"),
                sender_phone=sender_phone,
                text=body,
                timestamp=msg.get("timestamp", "")
            )
        except (IndexError, KeyError, TypeError) as e:
            logger.error("Failed to parse incoming WhatsApp payload: %s", str(e))
            return None

    @classmethod
    def find_or_create_conversation(
        cls, db: Session, sender_phone: str, deployment: Deployment
    ) -> Conversation:
        """
        Look up or create a conversation for a WhatsApp sender.
        Reuses the conversation if it exists, is ongoing, and is within the 24h window of activity.
        """
        from app.models.conversation import Message as DBMessage
        
        # Find latest active conversation for this sender and deployment
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.deployment_id == deployment.id,
                Conversation.sender_phone == sender_phone,
                Conversation.status.in_([ConversationStatus.ONGOING, ConversationStatus.ESCALATED]),
                Conversation.deleted_at == None
            )
            .order_by(Conversation.started_at.desc())
            .first()
        )
        
        now = datetime.now(timezone.utc)
        
        if conversation:
            # Check last message activity in this conversation
            last_message = (
                db.query(DBMessage)
                .filter(DBMessage.conversation_id == conversation.id)
                .order_by(DBMessage.created_at.desc())
                .first()
            )
            
            last_activity = last_message.created_at if last_message else conversation.started_at
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
                
            # If 24h inactive, resolve conversation and create a new session
            if now - last_activity > timedelta(hours=24):
                conversation.status = ConversationStatus.RESOLVED
                db.add(conversation)
                db.flush()
                conversation = None
                
        if not conversation:
            conversation = Conversation(
                chatbot_id=deployment.chatbot_id,
                deployment_id=deployment.id,
                sender_phone=sender_phone,
                status=ConversationStatus.ONGOING
            )
            db.add(conversation)
            db.flush()
            
        return conversation

    @classmethod
    def process_inbound_message(cls, db: Session, payload: dict) -> None:
        """
        Process the parsed message payload: find deployment, check idempotency,
        invoke the RAG chat service, and reply back to the user.
        """
        try:
            # Route by phone number ID
            entry = payload.get("entry", [])[0]
            change = entry.get("changes", [])[0]
            value = change.get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            
            if not phone_number_id:
                logger.warning("Incoming payload is missing phone_number_id metadata. Skipping.")
                return
                
            # Parse message content
            message = cls.parse_incoming_message(payload)
            if not message:
                return
                
            # Check idempotency
            processed = db.query(ProcessedEvent).filter(ProcessedEvent.event_id == message.message_id).first()
            if processed:
                logger.info("Event %s already processed. Skipping.", message.message_id)
                return
                
            # Find active deployment, ignoring any deployments linked to deleted chatbots
            deployment = (
                db.query(Deployment)
                .join(Chatbot, Deployment.chatbot_id == Chatbot.id)
                .filter(
                    Deployment.whatsapp_phone_number_id == phone_number_id,
                    Deployment.is_active == True,
                    Chatbot.deleted_at == None
                )
                .first()
            )
            
            if not deployment:
                logger.warning("No active WhatsApp deployment found for phone_number_id: %s", phone_number_id)
                return
                
            # Find or create session
            conversation = cls.find_or_create_conversation(db, message.sender_phone, deployment)
            
            # Fetch chatbot and org info
            chatbot = db.query(Chatbot).filter(Chatbot.id == deployment.chatbot_id).first()
            if not chatbot:
                logger.error("Chatbot not found for deployment %s", deployment.id)
                return
                
            # Invoke existing RAG pipeline
            result = ChatService.get_rag_response(
                db=db,
                org_id=chatbot.org_id,
                chatbot_id=chatbot.id,
                user_message=message.text,
                conversation_id=conversation.id,
                deployment_id=deployment.id
            )
            
            ai_response = result.get("response")
            
            # Enqueue outbound message job (same transaction)
            if ai_response:
                OutboxService.enqueue(
                    db=db,
                    conversation_id=conversation.id,
                    channel="whatsapp",
                    payload={
                        "phone_number": message.sender_phone,
                        "text": ai_response,
                        "phone_number_id": phone_number_id,
                    },
                )
            
            # Log event as processed
            event = ProcessedEvent(
                event_id=message.message_id,
                event_type="whatsapp_message"
            )
            db.add(event)
            db.commit()
            
        except Exception as e:
            logger.exception("Error processing WhatsApp message: %s", str(e))
            db.rollback()

    @classmethod
    def send_whatsapp_message(cls, phone_number: str, text: str, phone_number_id: str) -> dict:
        """
        Send reply back to WhatsApp using Meta's Cloud API.
        """
        if not settings.WHATSAPP_ACCESS_TOKEN:
            logger.warning(
                "WHATSAPP_ACCESS_TOKEN not configured. Message would have been: '%s' to %s",
                text, phone_number
            )
            return {"mock": True}
            
        url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }
        
        try:
            # We perform standard synchronous HTTP POST call using httpx
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=headers, json=body)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Meta WhatsApp API error response: %s", e.response.text)
            raise e
        except Exception as e:
            logger.error("Outbound WhatsApp connection failure: %s", str(e))
            raise e
