import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationStatus, Deployment, ProcessedEvent, Channel, Message as DBMessage
from app.models.chatbot import Chatbot
from app.services.chat import ChatService

logger = logging.getLogger(__name__)

class InboundMessageEvent(BaseModel):
    channel: Channel
    event_id: str
    phone_number_id: str
    sender_id: str
    text: str

class ChannelRouter:
    @classmethod
    def route(cls, db: Session, event: InboundMessageEvent) -> Optional[str]:
        """
        Route an inbound message event through the RAG pipeline.
        Handles event deduplication, session management, and database state updates.
        Returns the response text to be sent back, or None if skipped.
        """
        # 1. Idempotency Check
        processed = db.query(ProcessedEvent).filter(ProcessedEvent.event_id == event.event_id).first()
        if processed:
            logger.info("Event %s already processed. Skipping.", event.event_id)
            return None

        # 2. Find Active Deployment
        deployment = (
            db.query(Deployment)
            .filter(
                Deployment.whatsapp_phone_number_id == event.phone_number_id,
                Deployment.is_active == True
            )
            .first()
        )
        if not deployment:
            logger.warning("No active deployment found for phone_number_id: %s", event.phone_number_id)
            return None

        # 3. Find or Create Conversation (Session Management)
        conversation = cls._find_or_create_conversation(db, event.sender_id, deployment)

        # 4. Fetch Chatbot details
        chatbot = db.query(Chatbot).filter(Chatbot.id == deployment.chatbot_id).first()
        if not chatbot:
            logger.error("Chatbot not found for deployment %s", deployment.id)
            return None

        # 5. Invoke RAG Chat Service
        result = ChatService.get_rag_response(
            db=db,
            org_id=chatbot.org_id,
            chatbot_id=chatbot.id,
            user_message=event.text,
            conversation_id=conversation.id,
            deployment_id=deployment.id
        )
        ai_response = result.get("response")

        # 6. Save Processed Event & Commit Transaction
        processed_event = ProcessedEvent(
            event_id=event.event_id,
            event_type=f"{event.channel.value}_message"
        )
        db.add(processed_event)
        db.commit()

        return ai_response

    @classmethod
    def _find_or_create_conversation(
        cls, db: Session, sender_id: str, deployment: Deployment
    ) -> Conversation:
        """
        Find latest active conversation session or create a new one.
        Applies the 24-hour inactivity window to resolve stale sessions.
        """
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.deployment_id == deployment.id,
                Conversation.sender_phone == sender_id,
                Conversation.status == ConversationStatus.ONGOING,
                Conversation.deleted_at == None
            )
            .order_by(Conversation.started_at.desc())
            .first()
        )

        now = datetime.now(timezone.utc)

        if conversation:
            # Find last message in this conversation
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
                sender_phone=sender_id,
                status=ConversationStatus.ONGOING
            )
            db.add(conversation)
            db.flush()

        return conversation
