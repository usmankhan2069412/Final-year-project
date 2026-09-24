import structlog
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.language import detect_message_language
from app.services.rag.state import AgentState
from app.services.rag.helpers import (
    get_llm,
    last_bot_answer,
    should_transform_recent_conversation,
    recent_conversation_text,
    history_transform_clarifying_message,
    history_transform_unavailable_message
)
from app.services.rag.prompts import PromptCatalog

logger = structlog.get_logger()


async def history_transform_node(state: AgentState) -> AgentState:
    history = state.get("history") or []
    user_message = state.get("user_message", "")
    lang = detect_message_language(user_message, history)

    if should_transform_recent_conversation(user_message):
        target_type = "recent_conversation"
        target_text = recent_conversation_text(history)
    else:
        target_type = "last_bot_answer"
        target_text = last_bot_answer(history)

    if not target_text:
        logger.info(
            "history_transform_result",
            target_type="missing",
            transformed_chars=0,
        )
        return {
            "response": history_transform_clarifying_message(lang),
            "response_source": "history_transform",
            "sources": [],
            "context_text": "",
            "is_relevant": False,
            "validated_chunks_count": 0,
        }

    llm = get_llm(state, temperature=0.2)
    if not llm:
        logger.info(
            "history_transform_result",
            target_type=target_type,
            transformed_chars=0,
            no_llm=True,
        )
        return {
            "response": history_transform_unavailable_message(lang),
            "response_source": "history_transform",
            "sources": [],
            "context_text": "",
            "is_relevant": False,
            "validated_chunks_count": 0,
        }

    try:
        persona_name = getattr(state.get("persona"), "name", None) or "Aina Bot"
        traits = state.get("traits") or []
        sys_msg = SystemMessage(content=PromptCatalog.build_transform_system_prompt(persona_name, traits))
        human_msg = HumanMessage(content=PromptCatalog.build_transform_human_message(user_message, target_type, target_text))
        response_msg = await llm.ainvoke([sys_msg, human_msg])
        response = response_msg.content.strip()
        if not response:
            response = history_transform_unavailable_message(lang)

        logger.info(
            "history_transform_result",
            target_type=target_type,
            transformed_chars=len(response),
        )
        return {
            "response": response,
            "response_source": "history_transform",
            "sources": [],
            "context_text": "",
            "is_relevant": False,
            "validated_chunks_count": 0,
        }
    except Exception as e:
        logger.warning("history_transform_failed", error=str(e), target_type=target_type)
        return {
            "response": history_transform_unavailable_message(lang),
            "response_source": "history_transform",
            "sources": [],
            "context_text": "",
            "is_relevant": False,
            "validated_chunks_count": 0,
        }
