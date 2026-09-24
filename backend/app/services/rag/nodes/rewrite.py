import logging
from langchain_core.messages import SystemMessage, HumanMessage
from app.models.conversation import MessageRole
from app.services.rag.state import AgentState
from app.services.rag.helpers import get_llm
from app.services.rag.prompts import PromptCatalog

logger = logging.getLogger(__name__)


async def rewrite_node(state: AgentState) -> AgentState:
    # For rewriting, we don't need streaming
    llm = get_llm(state, temperature=0.0)
    user_msg = state.get("user_message", "")

    history = state.get("history") or []
    if not history or not llm:
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
        return {"rewritten_query": rewritten}
    except Exception as e:
        logger.warning(f"Query rewrite failed: {e}")
        return {"rewritten_query": user_msg}
