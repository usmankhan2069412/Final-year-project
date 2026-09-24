from app.services.rag.state import AgentState
from app.core.language import detect_message_language
from app.models.conversation import ConversationStatus
from app.services.rag.prompts import LocalizationCatalog


async def agent_handoff_node(state: AgentState) -> AgentState:
    persona = state.get("persona")
    lang = getattr(persona, "language", "en") if persona else "en"
    if lang == "multilingual":
        lang = detect_message_language(state.get("user_message", ""), state.get("history"))

    text = LocalizationCatalog.get_handoff_message(lang or "en")
    return {"response": text, "status": ConversationStatus.ESCALATED}
