import structlog
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.language import detect_message_language
from app.services.rag.helpers import get_llm, generate_mock_response
from app.services.rag.prompts import PromptCatalog, LocalizationCatalog
from app.services.rag.state import AgentState

logger = structlog.get_logger(__name__)


def is_fallback_response(ans: str, fb_msg: str) -> bool:
    """Checks if the generated response matches the fallback text or standard fallback messages."""
    if not ans:
        return True
    ans_clean = ans.strip().rstrip(".").lower()
    fb_clean = fb_msg.strip().rstrip(".").lower() if fb_msg else ""
    if fb_clean and (ans_clean == fb_clean or fb_clean in ans_clean):
        return True
    for msg in LocalizationCatalog.FALLBACK_MESSAGES.values():
        clean_m = msg.strip().rstrip(".").lower()
        if ans_clean == clean_m or clean_m in ans_clean:
            return True
    return False


async def rag_answer_node(state: AgentState) -> Dict[str, Any]:
    """
    RAG generation node:
    Synthesizes an answer strictly from validated context chunks aligned with the persona and traits.
    Falls back gracefully if no context is relevant or if generation fails.
    """
    persona = state.get("persona")
    lang = getattr(persona, "language", "en") if persona else "en"
    user_msg = state.get("user_message", "")
    if lang == "multilingual":
        lang = detect_message_language(user_msg, state.get("history"))

    fb_msg = (getattr(persona, "fallback", None) if persona else None) or LocalizationCatalog.get_fallback_message(lang or "en")

    if not state.get("is_relevant") or not state.get("context_text"):
        return {"response": fb_msg, "response_source": "fallback", "is_relevant": False}

    traits = state.get("traits") or []
    llm = get_llm(state)
    if llm:
        try:
            sys_prompt = PromptCatalog.build_rag_system_prompt(
                persona_name=(getattr(persona, "name", None) if persona else None) or "Aina Bot",
                traits=traits,
                description=getattr(persona, "description", None) if persona else None,
                context_text=state.get("context_text", ""),
                lang=lang,
                fallback_text=fb_msg,
            )
            search_query = state.get("rewritten_query") or user_msg
            human_content = PromptCatalog.build_rag_human_message(
                user_message=user_msg,
                search_query=search_query,
            )
            messages = [
                SystemMessage(content=sys_prompt),
                HumanMessage(content=human_content),
            ]

            ans_msg = await llm.ainvoke(messages)
            ans = ans_msg.content.strip()

            # Mark reply as fallback if it matches fallback text to prevent caching and erroneous analytics
            if is_fallback_response(ans, fb_msg):
                return {"response": ans, "response_source": "fallback", "is_relevant": False}

            return {"response": ans, "response_source": "rag_generation"}
        except Exception as e:
            logger.warning(f"RAG generation failed: {e}")

    # Mock fallback
    ans = generate_mock_response(
        state.get("rewritten_query") or user_msg,
        traits,
    )
    return {"response": ans, "response_source": "fallback", "is_relevant": False}
