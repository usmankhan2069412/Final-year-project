import uuid
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Set
from sqlalchemy import text, select
import structlog

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import resolve_openrouter_key
from app.core.metrics import memory_summarization_total
from app.models.conversation import Conversation, Message as DBMessage, MessageRole
from app.services.semantic_router import MEMORY_THRESHOLD, MEMORY_REFRESH_INTERVAL
from app.services.rag.prompts import PromptCatalog
from app.db.session import AsyncSessionLocal

logger = structlog.get_logger()


class ConversationMemoryService:
    """
    Dedicated service for managing and summarizing conversation memory.
    Encapsulates memory thresholds, LLM summarization, and safe background dispatch.
    """
    _background_tasks: Set[asyncio.Task] = set()

    @classmethod
    async def summarize_memory(
        cls,
        conversation_id: uuid.UUID,
        org_id: uuid.UUID,
        user_message: str,
        bot_response: str,
        api_key: str,
        history_len: int,
        memory: dict,
    ) -> None:
        """Conditionally summarize conversation memory in a background task natively async."""
        # Fast check without DB
        if history_len <= MEMORY_THRESHOLD:
            return

        if memory and memory.get("summary"):
            covered = memory.get("summary_covers_until_turn", 0)
            unsummarized = history_len - covered
            if unsummarized < MEMORY_REFRESH_INTERVAL:
                return

        if not api_key:
            return

        async with AsyncSessionLocal() as db:
            try:
                # Bind tenant context for Row-Level Security
                await db.execute(
                    text("SELECT set_config('app.current_org_id', :org_id, true)"),
                    {"org_id": str(org_id)},
                )

                result = await db.execute(select(Conversation).filter(Conversation.id == conversation_id))
                conv = result.scalar_one_or_none()
                if not conv:
                    return

                effective_key, base_url = resolve_openrouter_key(api_key)
                if not effective_key:
                    return

                llm_kwargs = {
                    "api_key": effective_key,
                    "model": "openai/gpt-4o-mini" if base_url else "gpt-4o-mini",
                    "temperature": 0.0,
                    "max_tokens": 150,
                }
                if base_url:
                    llm_kwargs["base_url"] = base_url

                llm = ChatOpenAI(**llm_kwargs)

                msg_filters = [
                    DBMessage.conversation_id == conversation_id,
                    DBMessage.created_at <= datetime.now(timezone.utc)
                ]
                if conv.started_at is not None:
                    msg_filters.append(DBMessage.created_at >= conv.started_at)

                result = await db.execute(
                    select(DBMessage).filter(*msg_filters).order_by(DBMessage.created_at.asc())
                )
                all_history = list(result.scalars().all())

                covered = memory.get("summary_covers_until_turn", 0) if memory else 0

                unsummarized_msgs = all_history[covered:] if covered < len(all_history) else all_history[-4:]

                if not unsummarized_msgs:
                    return

                msg_lines = []
                for m in unsummarized_msgs:
                    role_label = "USER" if m.role == MessageRole.USER else "BOT"
                    msg_lines.append(f"{role_label}: {m.content}")

                existing_summary = memory.get("summary", "") if memory else ""
                prev_context = f"Previous summary: {existing_summary}" if existing_summary else "Previous summary: None (new conversation)"

                sys_prompt = PromptCatalog.build_memory_summarization_prompt(prev_context, msg_lines)

                result_msg = await llm.ainvoke([
                    SystemMessage(content=sys_prompt),
                    HumanMessage(content="Generate the JSON:")
                ])
                result = result_msg.content.strip()

                if result.startswith("```"):
                    result = result.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

                parsed = json.loads(result)
                new_memory = {
                    "summary": parsed.get("summary", ""),
                    "turn_count": len(all_history),
                    "summary_covers_until_turn": len(all_history),
                    "topics": parsed.get("topics", []),
                    "user_mood": parsed.get("user_mood", "neutral"),
                    "phase": parsed.get("phase", "active"),
                }

                conv.memory = new_memory
                db.add(conv)
                await db.commit()

                memory_summarization_total.inc()
                logger.info("conversation_memory_updated", turn_count=len(all_history), phase=new_memory["phase"])
            except Exception as e:
                logger.warning(f"Background memory summarization failed: {e}")

    @classmethod
    def dispatch_background_summary(
        cls,
        background_tasks: Optional[Any] = None,
        **summ_kwargs,
    ) -> None:
        """
        Dispatches memory summarization in the background.
        Uses FastAPI BackgroundTasks when available, or a GC-safe tracked asyncio task.
        """
        if background_tasks:
            background_tasks.add_task(cls.summarize_memory, **summ_kwargs)
        else:
            task = asyncio.create_task(cls.summarize_memory(**summ_kwargs))
            cls._background_tasks.add(task)
            task.add_done_callback(cls._background_tasks.discard)
