import hmac
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

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
        try:
            entry = payload.get("entry", [])[0]
            change = entry.get("changes", [])[0]
            value = change.get("value", {})

            if change.get("field") != "messages":
                return None

            messages = value.get("messages", [])
            if not messages:
                return None

            msg = messages[0]
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
    async def find_or_create_conversation(
        cls, db: AsyncSession, sender_phone: str, deployment: Deployment
    ) -> Conversation:
        from app.models.conversation import Message as DBMessage

        stmt = (
            select(Conversation)
            .filter(
                Conversation.deployment_id == deployment.id,
                Conversation.sender_phone == sender_phone,
                Conversation.status.in_([ConversationStatus.ONGOING, ConversationStatus.ESCALATED]),
                Conversation.deleted_at == None
            )
            .order_by(Conversation.started_at.desc())
        )
        res = await db.execute(stmt)
        conversation = res.scalars().first()

        now = datetime.now(timezone.utc)

        if conversation:
            msg_stmt = (
                select(DBMessage)
                .filter(DBMessage.conversation_id == conversation.id)
                .order_by(DBMessage.created_at.desc())
            )
            msg_res = await db.execute(msg_stmt)
            last_message = msg_res.scalars().first()

            last_activity = last_message.created_at if last_message else conversation.started_at
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)

            if now - last_activity > timedelta(hours=24):
                conversation.status = ConversationStatus.RESOLVED
                db.add(conversation)
                await db.flush()
                conversation = None

        if not conversation:
            conversation = Conversation(
                chatbot_id=deployment.chatbot_id,
                deployment_id=deployment.id,
                sender_phone=sender_phone,
                status=ConversationStatus.ONGOING
            )
            db.add(conversation)
            await db.flush()

        return conversation

    @classmethod
    async def process_inbound_message(cls, payload: dict) -> None:
        """Process inbound WhatsApp messages in a background task.
        Creates its own async session."""
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            try:
                message = cls.parse_incoming_message(payload)
                if not message:
                    return

                entries = payload.get("entry", [])
                if not entries or not entries[0].get("changes"):
                    return
                value = entries[0]["changes"][0].get("value", {})
                phone_number_id = value.get("metadata", {}).get("phone_number_id")

                if not phone_number_id or not message.message_id:
                    logger.warning("Incoming payload is missing phone_number_id or message_id metadata. Skipping.")
                    return

                # Atomic deduplication claim:
                # Insert and commit ProcessedEvent immediately before starting RAG to prevent race conditions
                # when Meta sends concurrent webhook deliveries for the same incoming message.
                try:
                    event = ProcessedEvent(
                        event_id=message.message_id,
                        event_type="whatsapp_message"
                    )
                    db.add(event)
                    await db.commit()
                except IntegrityError:
                    await db.rollback()
                    logger.info("Event %s already processed or being processed concurrently. Skipping duplicate.", message.message_id)
                    return

                stmt_dep = (
                    select(Deployment)
                    .options(selectinload(Deployment.chatbot))
                    .join(Chatbot, Deployment.chatbot_id == Chatbot.id)
                    .filter(
                        Deployment.whatsapp_phone_number_id == phone_number_id,
                        Deployment.is_active == True,
                        Chatbot.deleted_at == None
                    )
                )
                res_dep = await db.execute(stmt_dep)
                deployment = res_dep.scalars().first()

                if not deployment:
                    logger.warning("No active WhatsApp deployment found for phone_number_id: %s", phone_number_id)
                    return

                conversation = await cls.find_or_create_conversation(db, message.sender_phone, deployment)

                stmt_cb = select(Chatbot).filter(Chatbot.id == deployment.chatbot_id)
                res_cb = await db.execute(stmt_cb)
                chatbot = res_cb.scalars().first()
                if not chatbot:
                    logger.error("Chatbot not found for deployment %s", deployment.id)
                    return

                # Bind tenant context for RLS
                await db.execute(
                    text("SELECT set_config('app.current_org_id', :org_id, true)"),
                    {"org_id": str(chatbot.org_id)}
                )

                result = await ChatService.aget_rag_response(
                    db=db,
                    org_id=chatbot.org_id,
                    chatbot_id=chatbot.id,
                    user_message=message.text,
                    conversation_id=conversation.id,
                    deployment_id=deployment.id
                )

                ai_response = result.get("response")

                if ai_response:
                    await OutboxService.enqueue(
                        db=db,
                        conversation_id=conversation.id,
                        channel="whatsapp",
                        payload={
                            "phone_number": message.sender_phone,
                            "text": ai_response,
                            "phone_number_id": phone_number_id,
                        },
                    )
                    await db.commit()

            except Exception as e:
                logger.exception("Error processing WhatsApp message: %s", str(e))
                await db.rollback()

    @classmethod
    def send_whatsapp_message(cls, phone_number: str, text: str, phone_number_id: str) -> dict:
        raw_token = settings.WHATSAPP_ACCESS_TOKEN or ""
        token = raw_token.strip().strip('"').strip("'")
        if not token:
            logger.warning(
                "WHATSAPP_ACCESS_TOKEN not configured. Message would have been: '%s' to %s",
                text, phone_number
            )
            return {"mock": True}

        version = settings.WHATSAPP_API_VERSION or "v21.0"
        if version.lower() in ("v25.0", "v25", ""):
            version = "v21.0"
        url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
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
