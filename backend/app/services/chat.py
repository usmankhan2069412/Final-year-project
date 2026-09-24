import uuid
import time
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks

from app.core.metrics import chat_requests_total, chat_latency_seconds, fallback_total, validated_chunks_count
from app.models.conversation import ConversationStatus

import structlog
logger = structlog.get_logger()

from app.services.rag.state import AgentState
from app.services.rag.helpers import close_async_http_client
from app.services.rag.nodes import (
    route_intent_node,
    history_transform_node,
    rewrite_node,
    validate_node,
    rag_answer_node,
)
from app.services.rag.graph import execute_rag_pipeline
from app.services.rag.retriever import PostgresRetriever
from app.services.chat_session_manager import ChatSessionManager, SessionContext
from app.services.memory import ConversationMemoryService


# --- Agent Graph Executor ---
class AgentGraphExecutor:
    """
    Facade class preserving backward compatibility for evaluators and test callers.
    Delegates active pipeline operations to modular app.services.rag components.
    """
    @classmethod
    async def close_async_http_client(cls):
        await close_async_http_client()

    # --- Node Methods (Evaluator & Test Targets) ---
    @staticmethod
    async def route_intent(state: AgentState) -> Dict[str, Any]:
        return await route_intent_node(state)

    @staticmethod
    async def history_transform_node(state: AgentState) -> Dict[str, Any]:
        return await history_transform_node(state)

    @staticmethod
    async def rewrite_node(state: AgentState) -> Dict[str, Any]:
        return await rewrite_node(state)

    @classmethod
    async def validate_node(cls, state: AgentState) -> Dict[str, Any]:
        return await validate_node(state)

    @staticmethod
    async def rag_answer_node(state: AgentState) -> Dict[str, Any]:
        return await rag_answer_node(state)

    # --- Pipeline Execution ---
    @classmethod
    async def aexecute(cls, initial_state: AgentState) -> AgentState:
        return await execute_rag_pipeline(initial_state)



# Single cache-sync mechanism: metaclass property forwards all class-level
# reads/writes to ChatSessionManager._model_config_cache (handles both
# mutation via .clear()/[]= and reassignment via = {}).
class _ChatServiceMeta(type):
    @property
    def _model_config_cache(cls) -> Dict[str, Tuple[float, Optional[str], Dict[str, str], Optional[uuid.UUID]]]:
        return ChatSessionManager._model_config_cache

    @_model_config_cache.setter
    def _model_config_cache(cls, value: Dict[str, Tuple[float, Optional[str], Dict[str, str], Optional[uuid.UUID]]]):
        ChatSessionManager._model_config_cache = value


# --- Chat Service Orchestrator ---
class ChatService(metaclass=_ChatServiceMeta):
    """
    Orchestrator class managing DB transactions, security, lookup, and updates.
    Invokes the pure AgentGraphExecutor for LangGraph execution.
    """

    _background_tasks: Set[asyncio.Task] = set()

    # Backward-compatibility alias preserving tests and callers patching ChatService.abackground_summarize_memory
    abackground_summarize_memory = ConversationMemoryService.summarize_memory

    @staticmethod
    async def route_intent(state: AgentState) -> Dict[str, Any]:
        return await AgentGraphExecutor.route_intent(state)

    @classmethod
    async def aget_rag_response(
        cls,
        db: AsyncSession,
        org_id: uuid.UUID,
        chatbot_id: uuid.UUID,
        user_message: str,
        conversation_id: Optional[uuid.UUID] = None,
        deployment_id: Optional[uuid.UUID] = None,
        callbacks: Optional[List[Any]] = None,
        background_tasks: Optional[BackgroundTasks] = None,
        status_queue: Optional[Any] = None,
    ) -> Dict[str, Any]:
        # 1. Prepare session & lifecycle state (fast-paths early if already escalated)
        ctx = await ChatSessionManager.prepare_session(
            db=db,
            org_id=org_id,
            chatbot_id=chatbot_id,
            user_message=user_message,
            conversation_id=conversation_id,
            deployment_id=deployment_id,
            background_tasks=background_tasks,
        )
        if ctx.early_response is not None:
            return ctx.early_response

        # 2. Pure in-memory graph execution
        if status_queue:
            await status_queue.put({"type": "status", "message": "📚 Searching knowledge base..."})
        initial_state = ctx.to_agent_state(
            callbacks=callbacks,
            status_queue=status_queue,
            retriever=PostgresRetriever(db=db),
        )
        t0 = time.monotonic()
        final_state = await AgentGraphExecutor.aexecute(initial_state)
        chat_latency_seconds.observe(time.monotonic() - t0)

        # 3. Observability & metrics
        val_chunks = final_state.get("validated_chunks_count", 0)
        validated_chunks_count.observe(val_chunks)
        response_text = final_state.get("response", "An error occurred during generation.")
        new_status = final_state.get("status", ctx.conversation.status)
        sources = final_state.get("sources", [])
        intent = final_state.get("intent", "unknown")

        response_source = final_state.get("response_source")
        is_cache_hit = response_source == "semantic_cache"
        is_relevant = final_state.get("is_relevant", False)
        is_direct_answer = response_source in {"history_transform", "conversational"}
        outcome = "answered" if (is_relevant or is_cache_hit or is_direct_answer or new_status == ConversationStatus.ESCALATED) else "fallback"
        chat_requests_total.labels(intent=intent or "unknown", outcome=outcome).inc()
        if outcome == "fallback":
            fallback_total.inc()

        # Mutually Exclusive Escalation Branch: Never falls through to record_bot_turn_and_transition
        if new_status == ConversationStatus.ESCALATED:
            from app.services.escalation_router import EscalationRouter
            return await EscalationRouter.aescalate(
                db=db,
                conversation=ctx.conversation,
                chatbot=ctx.chatbot,
                org_id=org_id,
                user_message=user_message,
                response_text=response_text,
                language=ctx.persona.language if ctx.persona else None,
                is_new_conv=ctx.is_new_conv,
                active_config_id=ctx.active_config_id,
                sources=sources,
                write_user_message=False,
                background_tasks=background_tasks,
            )

        # 4. State transition & message persistence
        await ChatSessionManager.record_bot_turn_and_transition(
            db=db,
            ctx=ctx,
            new_status=new_status,
            response_text=response_text,
        )

        # 5. Side-effects (cache insert & memory summarization)
        cls._dispatch_background_effects(
            final_state=final_state,
            ctx=ctx,
            response_text=response_text,
            sources=sources,
            intent=intent,
            background_tasks=background_tasks,
        )

        return {
            "response": response_text,
            "conversation_id": ctx.conversation.id,
            "status": new_status,
            "sources": sources,
        }

    @classmethod
    def _dispatch_background_effects(
        cls,
        final_state: Dict[str, Any],
        ctx: SessionContext,
        response_text: str,
        sources: List[Dict[str, Any]],
        intent: str,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> None:
        # Update cache on successful new RAG answers
        if (
            intent == "RAG_LOOKUP"
            and final_state.get("is_relevant")
            and final_state.get("response_source") == "rag_generation"
            and final_state.get("validated_chunks_count", 0) > 0
            and response_text
        ):
            rewritten_query = final_state.get("rewritten_query")
            source_chunk_ids = [src["chunk_id"] for src in sources] if sources else []
            if rewritten_query:
                from app.services.semantic_cache import SemanticCacheService
                task_kwargs = {
                    "org_id": str(ctx.org_id),
                    "chatbot_id": str(ctx.chatbot_id),
                    "rewritten_query": rewritten_query,
                    "response_text": response_text,
                    "knowledge_base_version": getattr(ctx.chatbot, "knowledge_base_version", 1),
                    "persona_version": getattr(ctx.persona, "persona_version", 1) if ctx.persona else 1,
                    "source_chunk_ids": source_chunk_ids,
                    "query_vector": final_state.get("query_vector"),
                }
                if background_tasks:
                    background_tasks.add_task(SemanticCacheService.aadd_to_cache, **task_kwargs)
                else:
                    async def _safe_cache_add():
                        try:
                            await SemanticCacheService.aadd_to_cache(**task_kwargs)
                        except Exception as e:
                            logger.warning(f"Background semantic cache insert failed: {e}")
                    cache_task = asyncio.create_task(_safe_cache_add())
                    cls._background_tasks.add(cache_task)
                    cache_task.add_done_callback(cls._background_tasks.discard)

        # Queue background summarization with patchable alias and GC tracking
        summ_kwargs = {
            "conversation_id": ctx.conversation.id,
            "org_id": ctx.org_id,
            "user_message": ctx.user_message,
            "bot_response": response_text,
            "api_key": ctx.api_key,
            "history_len": len(ctx.history) + 1,
            "memory": ctx.conversation.memory,
        }
        if background_tasks:
            background_tasks.add_task(cls.abackground_summarize_memory, **summ_kwargs)
        else:
            summ_task = asyncio.create_task(cls.abackground_summarize_memory(**summ_kwargs))
            cls._background_tasks.add(summ_task)
            summ_task.add_done_callback(cls._background_tasks.discard)


    @classmethod
    async def async_get_rag_response(
        cls, db: AsyncSession, org_id: uuid.UUID, chatbot_id: uuid.UUID, user_message: str, conversation_id: Optional[uuid.UUID] = None, deployment_id: Optional[uuid.UUID] = None, callbacks: Optional[List[Any]] = None, background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """Async version of get_rag_response. Now natively async!"""
        return await cls.aget_rag_response(
            db=db,
            org_id=org_id,
            chatbot_id=chatbot_id,
            user_message=user_message,
            conversation_id=conversation_id,
            deployment_id=deployment_id,
            callbacks=callbacks,
            background_tasks=background_tasks,
        )

    # Alias preserved for tests patching ChatService.get_rag_response (e.g. test_whatsapp.py:205)
    get_rag_response = aget_rag_response

    @classmethod
    async def aget_rag_stream(
        cls, db: AsyncSession, org_id: uuid.UUID, chatbot_id: uuid.UUID, user_message: str, conversation_id: Optional[uuid.UUID] = None, deployment_id: Optional[uuid.UUID] = None, background_tasks: Optional[BackgroundTasks] = None
    ):
        from app.services.streaming import AsyncStreamingCallbackHandler

        q = asyncio.Queue()
        handler = AsyncStreamingCallbackHandler(q)

        async def run_async():
            try:
                await q.put({"type": "status", "message": "🔍 Understanding your question..."})
                res = await cls.aget_rag_response(
                    db=db, org_id=org_id, chatbot_id=chatbot_id, user_message=user_message, conversation_id=conversation_id, deployment_id=deployment_id, callbacks=[handler], background_tasks=background_tasks, status_queue=q
                )
                await q.put({"type": "final", "data": res})
            except Exception as e:
                logger.error(f"Error in RAG streaming task: {e}", exc_info=True)
                await q.put({"type": "error", "error": str(e)})
            finally:
                await q.put(None)  # Sentinel

        stream_task = asyncio.create_task(run_async())
        cls._background_tasks.add(stream_task)
        stream_task.add_done_callback(cls._background_tasks.discard)

        while True:
            token = await q.get()
            if token is None:
                break
            if isinstance(token, dict) and "type" in token:
                if token["type"] == "status":
                    yield f"data: {json.dumps(token)}\n\n"
                elif token["type"] == "final":
                    res = token["data"]
                    res["conversation_id"] = str(res["conversation_id"])
                    if "status" in res and hasattr(res["status"], "value"):
                        res["status"] = res["status"].value
                    for src in res.get("sources", []):
                        if "chunk_id" in src: src["chunk_id"] = str(src["chunk_id"])
                        if "source_id" in src: src["source_id"] = str(src["source_id"])
                    yield f"data: {json.dumps({'type': 'final', 'data': res})}\n\n"
                elif token["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'error': token['error']})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        yield "data: [DONE]\n\n"


__all__ = [
    "ChatService",
    "ChatSessionManager",
    "SessionContext",
    "AgentGraphExecutor",
    "AgentState",
    "ConversationMemoryService",
]
