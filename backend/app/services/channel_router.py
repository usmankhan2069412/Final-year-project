import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

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
    async def aroute(cls, db: AsyncSession, event: InboundMessageEvent) -> Optional[str]:
        """
        Async route for an inbound message event through the RAG pipeline.
        Handles event deduplication, session management, and database state updates.
        Returns the response text to be sent back, or None if skipped.
        """
        # 1. Atomic Idempotency Check & Claim
        try:
            db.add(ProcessedEvent(
                event_id=event.event_id,
                event_type=f"{event.channel.value}_message"
            ))
            await db.commit()
        except IntegrityError:
            await db.rollback()
            logger.info("Event %s already processed or being processed concurrently. Skipping duplicate.", event.event_id)
            return None

        # 2. Find Active Deployment
        result = await db.execute(
            select(Deployment).filter(
                Deployment.whatsapp_phone_number_id == event.phone_number_id,
                Deployment.is_active == True
            )
        )
        deployment = result.scalar_one_or_none()
        if not deployment:
            logger.warning("No active deployment found for phone_number_id: %s", event.phone_number_id)
            return None

        # 3. Find or Create Conversation (Session Management)
        conversation = await cls._afind_or_create_conversation(db, event.sender_id, deployment)

        # 4. Fetch Chatbot details
        result = await db.execute(
            select(Chatbot).filter(Chatbot.id == deployment.chatbot_id)
        )
        chatbot = result.scalar_one_or_none()
        if not chatbot:
            logger.error("Chatbot not found for deployment %s", deployment.id)
            return None

        # 5. Invoke RAG Chat Service (awaited — never return an unawaited coroutine)
        result_data = await ChatService.aget_rag_response(
            db=db,
            org_id=chatbot.org_id,
            chatbot_id=chatbot.id,
            user_message=event.text,
            conversation_id=conversation.id,
            deployment_id=deployment.id
        )
        ai_response = result_data.get("response")

        return ai_response

    @classmethod
    def route(cls, *args, **kwargs):
        """Deprecated sync entry point. Use `await ChannelRouter.aroute(db, event)` with AsyncSession."""
        raise RuntimeError("ChannelRouter.route is deprecated: use await ChannelRouter.aroute(db, event) with AsyncSession")

    @classmethod
    async def _afind_or_create_conversation(
        cls, db: AsyncSession, sender_id: str, deployment: Deployment
    ) -> Conversation:
        """
        Find latest active conversation session or create a new one.
        Applies the 24-hour inactivity window to resolve stale sessions.
        """
        result = await db.execute(
            select(Conversation)
            .filter(
                Conversation.deployment_id == deployment.id,
                Conversation.sender_phone == sender_id,
                Conversation.status == ConversationStatus.ONGOING,
                Conversation.deleted_at == None
            )
            .order_by(Conversation.started_at.desc())
        )
        conversation = result.scalars().first()

        now = datetime.now(timezone.utc)

        if conversation:
            # Find last message in this conversation
            msg_result = await db.execute(
                select(DBMessage)
                .filter(DBMessage.conversation_id == conversation.id)
                .order_by(DBMessage.created_at.desc())
            )
            last_message = msg_result.scalars().first()

            last_activity = last_message.created_at if last_message else conversation.started_at
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)

            # If 24h inactive, resolve conversation and create a new session
            if now - last_activity > timedelta(hours=24):
                conversation.status = ConversationStatus.RESOLVED
                db.add(conversation)
                await db.flush()
                conversation = None

        if not conversation:
            conversation = Conversation(
                chatbot_id=deployment.chatbot_id,
                deployment_id=deployment.id,
                sender_phone=sender_id,
                status=ConversationStatus.ONGOING
            )
            db.add(conversation)
            await db.flush()

        return conversation

    @classmethod
    def _find_or_create_conversation(cls, *args, **kwargs):
        """Deprecated sync helper. Use `await _afind_or_create_conversation(db, sender_id, deployment)`."""
        raise RuntimeError("ChannelRouter._find_or_create_conversation is deprecated: use await _afind_or_create_conversation with AsyncSession")
