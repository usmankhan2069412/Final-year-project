import re
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from app.core.config import settings, resolve_openrouter_key
from app.models.conversation import MessageRole
from app.services.rag.state import AgentState


def get_llm(state: AgentState, temperature: float = 0.3, stream: bool = True) -> Optional[ChatOpenAI]:
    api_key = state.get("api_key")
    if not api_key:
        return None

    model = state.get("model_name", "openai/gpt-4o-mini")
    callbacks = state.get("callbacks") if stream else None

    effective_key, base_url = resolve_openrouter_key(api_key)
    if not effective_key:
        return None

    model_to_use = model if base_url else (model.split("/")[-1] if "/" in model else model)

    llm_kwargs = {
        "api_key": effective_key,
        "model": model_to_use,
        "temperature": temperature,
        "streaming": bool(callbacks),
        "callbacks": callbacks,
    }
    if base_url:
        llm_kwargs["base_url"] = base_url

    return ChatOpenAI(**llm_kwargs)



def content_terms(text: str) -> set[str]:
    stop_words = {
        "the", "and", "for", "are", "you", "your", "with", "that", "this", "what", "when", "where",
        "how", "why", "can", "could", "would", "should", "about", "from", "into", "have", "has",
        "hai", "hain", "kya", "aur", "mein", "mujhe", "aap", "ap", "ke", "ki", "ka", "ko", "se",
    }
    return {
        word
        for word in re.findall(r"\w+", text.lower())
        if len(word) > 2 and word not in stop_words
    }


def has_lexical_relevance(query: str, context: str) -> bool:
    query_terms = content_terms(query)
    if not query_terms or not context.strip():
        return False

    context_terms = content_terms(context)
    overlap = query_terms & context_terms
    if not overlap:
        return False

    overlap_ratio = len(overlap) / max(len(query_terms), 1)
    if len(query_terms) <= 2:
        return len(overlap) == len(query_terms)
    return len(overlap) >= 3 or overlap_ratio >= 0.6


def filter_lexically_relevant_sources(query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        source
        for source in sources
        if has_lexical_relevance(query, source.get("text", ""))
    ]


def filter_hybrid_relevant_sources(query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Semantic-first fallback: use dense_distance when available, else lexical overlap."""
    filtered = []
    for src in sources:
        dist = src.get("dense_distance")
        # Semantic check — handles stemming, tense, and multilingual variation
        if dist is not None and dist <= settings.RERANK_FALLBACK_SIMILARITY_THRESHOLD:
            filtered.append(src)
        # Lexical fallback — for cache hits or sparse-only results lacking dense distance
        elif has_lexical_relevance(query, src.get("text", "")):
            filtered.append(src)
    return filtered


def context_from_sources(sources: List[Dict[str, Any]]) -> str:
    return "\n\n".join(
        f"[Source {i + 1}]\n{text}"
        for i, text in enumerate(chunk.get("text") for chunk in sources if chunk.get("text"))
    )


def message_role_value(message: Any) -> str:
    role = message.get("role") if isinstance(message, dict) else getattr(message, "role", None)
    return getattr(role, "value", role) or ""


def message_content(message: Any) -> str:
    return (message.get("content") if isinstance(message, dict) else getattr(message, "content", "")) or ""


def last_bot_answer(history: List[Any]) -> str:
    for message in reversed(history or []):
        if message_role_value(message) == MessageRole.BOT.value:
            content = message_content(message).strip()
            if content:
                return content
    return ""


def should_transform_recent_conversation(user_message: str) -> bool:
    msg = user_message.lower()
    conversation_markers = [
        "our chat", "our conversation", "this chat", "full conversation",
        "chat history", "conversation history", "hamari baat", "hamari chat",
        "poori chat", "puri chat", "sari chat",
    ]
    summary_markers = ["summarize", "summarise", "summary", "khulasa", "mukhtasar"]
    return any(marker in msg for marker in conversation_markers) and any(marker in msg for marker in summary_markers)


def recent_conversation_text(history: List[Any], limit: int = 8) -> str:
    lines = []
    for message in (history or [])[-limit:]:
        role = message_role_value(message)
        content = message_content(message).strip()
        if not content:
            continue
        role_label = "User" if role == MessageRole.USER.value else "Assistant"
        lines.append(f"{role_label}: {content}")
    return "\n".join(lines)


def history_transform_clarifying_message(lang: str) -> str:
    from app.services.rag.prompts import LocalizationCatalog
    return LocalizationCatalog.get_clarifying_message(lang)


def history_transform_unavailable_message(lang: str) -> str:
    from app.services.rag.prompts import LocalizationCatalog
    return LocalizationCatalog.get_unavailable_message(lang)


def fallback_message(lang: str) -> str:
    from app.services.rag.prompts import LocalizationCatalog
    return LocalizationCatalog.get_fallback_message(lang)


def generate_mock_response(query: str, traits: List[str]) -> str:
    from app.core.language import detect_message_language
    from app.services.rag.prompts import LocalizationCatalog
    lang = detect_message_language(query)
    return LocalizationCatalog.get_mock_response(lang, traits)


_async_http_client: Optional[Any] = None


def get_async_http_client():
    global _async_http_client
    import httpx
    if _async_http_client is None or _async_http_client.is_closed:
        _async_http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=settings.EMBEDDING_MAX_KEEPALIVE,
                max_connections=settings.EMBEDDING_MAX_CONNECTIONS,
            ),
        )
    return _async_http_client


async def close_async_http_client():
    global _async_http_client
    if _async_http_client is not None and not _async_http_client.is_closed:
        await _async_http_client.aclose()
        _async_http_client = None

