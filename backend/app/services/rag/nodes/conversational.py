import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.core.language import detect_message_language
from app.models.conversation import MessageRole
from app.services.rag.state import AgentState
from app.services.rag.helpers import get_llm, message_role_value, message_content
from app.services.rag.prompts import PromptCatalog

logger = logging.getLogger(__name__)


async def conversational_node(state: AgentState) -> AgentState:
    llm = get_llm(state, temperature=0.7)
    greeting = getattr(state.get("persona"), "greeting", None) or "Hello! How can I help you today?"

    if llm:
        try:
            detected_lang = detect_message_language(state.get("user_message", ""), state.get("history"))
            persona = state.get("persona")
            desc = getattr(persona, "description", None) or ""
            memory = state.get("conversation_memory")
            memory_summary = memory.get("summary") if memory else None
            persona_name = getattr(persona, "name", None) or "Aina Bot"

            sys_content = PromptCatalog.build_conversational_system_prompt(
                persona_name=persona_name,
                traits=state.get("traits") or [],
                description=desc,
                memory_summary=memory_summary,
                greeting=greeting,
                lang=detected_lang,
            )
            sys_msg = SystemMessage(content=sys_content)
            messages = [sys_msg]
            for m in (state.get("history") or [])[-6:]:
                role_val = message_role_value(m)
                content = message_content(m)
                role_cls = HumanMessage if role_val in (MessageRole.USER.value, "user", "human") else AIMessage
                messages.append(role_cls(content=content))
            messages.append(HumanMessage(content=state.get("user_message", "")))

            result_msg = await llm.ainvoke(messages)
            result = result_msg.content.strip()
            return {"response": result, "response_source": "conversational"}
        except Exception as e:
            logger.warning(f"LLM conversational generation failed: {e}")

    return {"response": greeting, "response_source": "conversational"}
