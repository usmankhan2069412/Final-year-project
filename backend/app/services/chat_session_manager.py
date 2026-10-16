import uuid
import time
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, update
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks

from app.models.chatbot import Chatbot
from app.models.conversation import Conversation, ConversationStatus, Message as DBMessage, MessageRole
from app.models.persona import Persona
from app.models.ai_model import AIModelConfig
from app.services.bot import model_config_service
from app.services.rag.state import AgentState

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    org_id: uuid.UUID
    chatbot_id: uuid.UUID
    user_message: str
    chatbot: Chatbot
    conversation: Conversation
    is_new_conv: bool = False
    persona: Optional[Persona] = None
    traits: List[str] = field(default_factory=list)
    history: List[DBMessage] = field(default_factory=list)
    active_config_id: Optional[uuid.UUID] = None
    api_key: Optional[str] = None
    routing_rules_dict: Dict[str, str] = field(default_factory=dict)
    early_response: Optional[Dict[str, Any]] = None

    def to_agent_state(
        self,
        callbacks: Optional[List[Any]] = None,
        status_queue: Optional[Any] = None,
        retriever: Optional[Any] = None,
    ) -> AgentState:
        """
        Produces exact 18-key AgentState matching chat.py:495-514 pipeline contract.
        """
        return {
            "user_message": self.user_message,
            "history": self.history,
            "api_key": self.api_key,
            "model_name": "openai/gpt-4o-mini",  # Will be overwritten by routing rules
            "persona": self.persona,
            "traits": self.traits,
            "chatbot_id": str(self.chatbot_id),
            "status": self.conversation.status,
            "sources": [],
            "routing_rules": self.routing_rules_dict,
            "default_model": "openai/gpt-4o-mini",
            "callbacks": callbacks,
            "conversation_memory": self.conversation.memory,
            "org_id": str(self.org_id),
            "knowledge_base_version": getattr(self.chatbot, "knowledge_base_version", 1),
            "persona_version": getattr(self.persona, "persona_version", 1) if self.persona else 1,
            "status_queue": status_queue,
            "retriever": retriever,
        }


class ChatSessionManager:
    """
    Manages session lifecycle, conversation retrieval/creation, human-escalation fast paths,
    AI model config resolution, history windowing, and turn persistence.
    """
    _model_config_cache: Dict[str, Tuple[float, Optional[str], Dict[str, str], Optional[uuid.UUID]]] = {}

    @classmethod
    async def resolve_model_config(
        cls,
        db: AsyncSession,
        org_id: uuid.UUID
    ) -> Tuple[Optional[str], Dict[str, str], Optional[uuid.UUID]]:
        """
        Resolves active AI model configuration (API key, routing rules, config ID)
        with 60-second in-memory TTL caching.
        """
        org_id_str = str(org_id)
        cached_config = cls._model_config_cache.get(org_id_str)
        now_ts = time.monotonic()
        active_config_id: Optional[uuid.UUID] = None

        if cached_config and (now_ts - cached_config[0]) < 60.0:
            _, api_key, routing_rules_dict, active_config_id = cached_config
            return api_key, routing_rules_dict, active_config_id

        result = await db.execute(
            select(AIModelConfig)
            .options(selectinload(AIModelConfig.routing_rules))
            .filter(
                AIModelConfig.org_id == org_id,
                AIModelConfig.is_active == True,
            )
            .order_by(AIModelConfig.is_default.desc())
            .limit(1)
        )
        active_config = result.scalar_one_or_none()
        api_key = None
        routing_rules_dict = {}

        if active_config:
            active_config_id = active_config.id
            try:
                api_key = model_config_service.decrypt_key(active_config.encrypted_api_key)
            except Exception:
                pass
            for rule in active_config.routing_rules:
                if rule.is_active:
                    routing_rules_dict[rule.intent] = active_config.model_name

        if not api_key:
            api_key = "managed-by-openrouter"

        cls._model_config_cache[org_id_str] = (now_ts, api_key, routing_rules_dict, active_config_id)
        return api_key, routing_rules_dict, active_config_id

    @classmethod
    async def prepare_session(
        cls,
        db: AsyncSession,
        org_id: uuid.UUID,
        chatbot_id: uuid.UUID,
        user_message: str,
        conversation_id: Optional[uuid.UUID] = None,
        deployment_id: Optional[uuid.UUID] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> SessionContext:
        """
        Prepares conversation context with strict step ordering:
        1. Fetch Chatbot (+ joined Persona + Traits).
        2. Resolve Conversation session.
        3. ESCALATED Fast-Path: Bypasses Persona, AI Model, and RAG completely.
        4. RESOLVED auto-resume: Transitions to ONGOING.
        5. Persona & Traits validation: Only validated for active/resumed turns.
        6. AI Model configuration resolution.
        7. History windowing query.
        8. Record user turn & flush.
        """
        # 1. Fetch Chatbot + Persona + Traits in a SINGLE joined round-trip
        result = await db.execute(
            select(Chatbot)
            .options(joinedload(Chatbot.persona).selectinload(Persona.traits))
            .filter(
                Chatbot.id == chatbot_id,
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
        )
        chatbot = result.scalar_one_or_none()
        if not chatbot:
            raise ValueError("Chatbot not found or inaccessible")

        # 2. Resolve session & Fast-Path for Escalated Conversations
        is_new_conv = False
        if conversation_id:
            result = await db.execute(
                select(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.chatbot_id == chatbot_id,
                    Conversation.deleted_at == None
                )
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise ValueError("Conversation session not found")

            logger.info(f"[ESCALATION DEBUG] Found conversation {conversation_id}, status={conversation.status}")

            # 3. FAST-PATH: If already escalated, bypass Persona, AI Model, and RAG initialization completely
            if conversation.status == ConversationStatus.ESCALATED:
                logger.info(f"[ESCALATION DEBUG] Conversation {conversation.id} is ESCALATED → FAST-PATH handle_escalated_message")
                from app.services.escalation_router import EscalationRouter
                early_res = await EscalationRouter.ahandle_escalated_message(
                    db=db,
                    conversation=conversation,
                    chatbot=chatbot,
                    org_id=org_id,
                    user_message=user_message,
                    language=None,
                    active_config_id=None,
                    background_tasks=background_tasks
                )
                return SessionContext(
                    org_id=org_id,
                    chatbot_id=chatbot_id,
                    user_message=user_message,
                    chatbot=chatbot,
                    conversation=conversation,
                    is_new_conv=False,
                    early_response=early_res
                )

            # 4. If resolved, auto-resume bot
            if conversation.status == ConversationStatus.RESOLVED:
                conversation.status = ConversationStatus.ONGOING
                conversation.assigned_agent_id = None
                db.add(conversation)
                await db.flush()
        else:
            logger.info("[ESCALATION DEBUG] No conversation_id provided, creating new conversation")
            conversation = Conversation(
                chatbot_id=chatbot_id,
                status=ConversationStatus.ONGOING,
                deployment_id=deployment_id
            )
            db.add(conversation)
            await db.flush()
            is_new_conv = True

        # 5. Resolve Persona & Traits directly from joined Chatbot (Zero extra DB query!)
        persona = chatbot.persona
        if not persona:
            raise ValueError("Chatbot Persona not found")

        traits = [t.trait_name for t in persona.traits]

        # 6. Resolve AI Model configuration (Cached with 60s TTL + single query fallback)
        api_key, routing_rules_dict, active_config_id = await cls.resolve_model_config(db, org_id)

        logger.info(f"[ESCALATION DEBUG] Conversation {conversation.id} status={conversation.status} → proceeding with AI pipeline")

        # 7. History windowing query
        start_date = conversation.started_at
        end_date = datetime.now(timezone.utc)
        filters = [
            DBMessage.conversation_id == conversation.id,
            DBMessage.created_at <= end_date,
        ]
        if start_date is not None:
            filters.append(DBMessage.created_at >= start_date)

        result = await db.execute(
            select(DBMessage).filter(*filters).order_by(DBMessage.created_at.asc())
        )
        history = list(result.scalars().all())

        # 8. Record user message first to avoid ghost turns on execution failure
        user_msg = DBMessage(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_message,
            config_id=active_config_id
        )
        db.add(user_msg)
        await db.execute(
            update(Chatbot).where(Chatbot.id == chatbot.id).values(total_messages=Chatbot.total_messages + 1)
        )
        await db.flush()

        return SessionContext(
            org_id=org_id,
            chatbot_id=chatbot_id,
            user_message=user_message,
            chatbot=chatbot,
            conversation=conversation,
            is_new_conv=is_new_conv,
            persona=persona,
            traits=traits,
            history=history,
            active_config_id=active_config_id,
            api_key=api_key,
            routing_rules_dict=routing_rules_dict,
            early_response=None,
        )

    @classmethod
    async def record_bot_turn_and_transition(
        cls,
        db: AsyncSession,
        ctx: SessionContext,
        new_status: ConversationStatus,
        response_text: str,
    ) -> None:
        """
        Records bot response message, applies status transitions, updates chatbot
        turn metrics, and commits the transaction.
        NOTE: Must NOT be called when escalated via EscalationRouter.aescalate,
        as aescalate manages its own message recording, broadcast, and commit.
        """
        try:
            if new_status != ctx.conversation.status:
                ctx.conversation.status = new_status
                db.add(ctx.conversation)

            db.add(DBMessage(
                conversation_id=ctx.conversation.id,
                role=MessageRole.BOT,
                content=response_text,
                config_id=ctx.active_config_id
            ))

            await db.execute(
                update(Chatbot).where(Chatbot.id == ctx.chatbot.id).values(total_messages=Chatbot.total_messages + 1)
            )
            if ctx.is_new_conv:
                await db.execute(
                    update(Chatbot).where(Chatbot.id == ctx.chatbot.id).values(total_conversations=Chatbot.total_conversations + 1)
                )

            await db.commit()
        except Exception as e:
            # If the transaction was invalidated by an upstream cancellation, rollback cleanly and persist the turn
            logger.warning(f"Initial record_bot_turn failed ({e}), attempting recovery after rollback")
            await db.rollback()
            try:
                db.add(DBMessage(
                    conversation_id=ctx.conversation.id,
                    role=MessageRole.BOT,
                    content=response_text,
                    config_id=ctx.active_config_id
                ))
                await db.commit()
            except Exception as inner_e:
                logger.error(f"Failed to record bot turn after rollback: {inner_e}")
                raise e
