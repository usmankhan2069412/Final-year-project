import structlog
from app.services.rag.state import AgentState
from app.services.semantic_router import SemanticRouter

logger = structlog.get_logger()


async def route_intent_node(state: AgentState) -> AgentState:
    chatbot_id = state.get("chatbot_id")
    model_name = state.get("default_model", "openai/gpt-4o-mini")
    rules = state.get("routing_rules", {})

    try:
        # Persona-aware, context-aware intent classification and decision gates via TypeSafe Jev / SemanticRouter
        intent, confidence, probabilities, method, gates = await SemanticRouter.classify_intent_and_gates(
            message=state.get("user_message", ""),
            persona=state.get("persona"),
            traits=state.get("traits"),
            history=state.get("history"),
            conversation_memory=state.get("conversation_memory"),
            api_key=state.get("api_key"),
        )
        final_intent = intent if intent else "RAG_LOOKUP"
    except Exception as e:
        logger.warning("route_intent_node_failed_falling_back", error=str(e), chatbot_id=chatbot_id)
        final_intent = "RAG_LOOKUP"
        confidence = 0.0
        probabilities = {}
        method = "fallback"
        gates = {"needs_rewrite": None, "needs_rewrite_p": 0.5}

    # Match intent to configured model, fallback to default OpenRouter model
    if final_intent in rules:
        model_name = rules[final_intent]
    elif "General Inquiries" in rules:
        model_name = rules["General Inquiries"]

    logger.info(
        "intent_routed",
        intent=final_intent,
        confidence=confidence,
        method=method,
        chatbot_id=chatbot_id,
        mapped_model=model_name,
        needs_rewrite=gates.get("needs_rewrite"),
    )
    return {
        "intent": final_intent,
        "intent_confidence": confidence,
        "intent_probabilities": probabilities,
        "intent_method": method,
        "model_name": model_name,
        "needs_rewrite": gates.get("needs_rewrite"),
        "needs_rewrite_confidence": gates.get("needs_rewrite_p"),
    }
