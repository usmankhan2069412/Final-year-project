import re
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from app.models.conversation import MessageRole
from app.services.rag.state import AgentState
from app.services.rag.helpers import get_llm
from app.services.rag.prompts import PromptCatalog

logger = logging.getLogger(__name__)

FOLLOWUP_PRONOUNS_AND_MARKERS = {
    # English pure anaphoric pronouns & determiners
    "it", "its", "this", "that", "these", "those",
    "he", "him", "his", "she", "her", "hers", "they", "them", "their", "theirs",
    # Roman Urdu / Urdu pure oblique & possessive anaphora
    "isay", "ise", "isko", "usko", "inko", "inhe", "unko", "unka", "inka",
    "iska", "uska", "iski", "uski", "pichla", "pichlay",
}


def has_followup_reference(text: str) -> bool:
    """Checks if text contains anaphoric pronouns or follow-up markers in <0.01ms."""
    if not text:
        return False
    words = set(re.findall(r"\b\w+\b", text.lower()))
    return bool(words & FOLLOWUP_PRONOUNS_AND_MARKERS)


async def rewrite_node(state: AgentState) -> AgentState:
    user_msg = state.get("user_message", "")
    history = state.get("history") or []

    # 1. First-turn bypass: empty history needs no rewriting
    if not history:
        return {"rewritten_query": user_msg}

    # 2. Jev Gate check with local safety net override
    needs_rw = state.get("needs_rewrite")
    if needs_rw is False:
        if not has_followup_reference(user_msg):
            logger.info("rewrite_bypassed_by_jev_gate", extra={"query": user_msg})
            return {"rewritten_query": user_msg}
        logger.info("rewrite_jev_false_negative_overridden", extra={"query": user_msg})

    # For rewriting, we don't need streaming
    llm = get_llm(state, temperature=0.0)
    if not llm:
        return {"rewritten_query": user_msg}

    try:
        history_str = ""
        for m in history[-4:]:
            if hasattr(m, "role"):
                role_label = "USER" if m.role == MessageRole.USER else "BOT"
            elif isinstance(m, HumanMessage) or getattr(m, "type", "") == "human":
                role_label = "USER"
            elif isinstance(m, dict):
                role_label = "USER" if m.get("role") in ("user", "human") else "BOT"
            else:
                role_label = "BOT"
            content = getattr(m, "content", "") or (m.get("content", "") if isinstance(m, dict) else str(m))
            history_str += f"{role_label}: {content}\n"

        sys_msg = SystemMessage(content=PromptCatalog.build_rewrite_system_prompt())
        h_msg = HumanMessage(content=PromptCatalog.build_rewrite_human_message(history_str, user_msg))

        rewritten_msg = await llm.ainvoke([sys_msg, h_msg])
        rewritten = rewritten_msg.content.strip()
        if rewritten.startswith('"') and rewritten.endswith('"'):
            rewritten = rewritten[1:-1]
        logger.info("query_rewritten: '%s' -> '%s'", user_msg, rewritten)
        return {"rewritten_query": rewritten}
    except Exception as e:
        logger.warning(f"Query rewrite failed: {e}")
        return {"rewritten_query": user_msg}
