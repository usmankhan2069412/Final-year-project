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



STOP_WORDS = {
    # English auxiliary & conversational fillers
    "the", "and", "for", "are", "you", "your", "with", "that", "this", "what", "when", "where",
    "how", "why", "can", "could", "would", "should", "about", "from", "into", "have", "has", "had",
    "does", "did", "tell", "give", "show", "know", "want", "need", "please", "help", "much", "many",
    "any", "some", "which", "there", "their", "they", "them", "been", "being", "will", "shall",
    # Roman Urdu auxiliaries & conversational fillers
    "hai", "hain", "kya", "aur", "mein", "mujhe", "aap", "ap", "ke", "ki", "ka", "ko", "se", "ho",
    "hoon", "hun", "bhi", "tou", "to", "kr", "kar", "karna", "karein", "karta", "karte", "raha",
    "rahi", "rha", "rhi", "kab", "sab", "hum", "tum", "kese", "kaise", "batao", "bataen", "batae",
    "chahiye", "chaheye", "hoga", "hogi", "theek", "thik", "acha", "achha", "karo", "pata", "kuch"
}


def content_terms(text: str) -> set[str]:
    """Extracts lowercase substantive content words from text, excluding conversational stop words."""
    if not text:
        return set()
    return {
        word
        for word in re.findall(r"\b\w+\b", text.lower())
        if len(word) > 2 and word not in STOP_WORDS
    }


def extract_key_anchors(text: str) -> set[str]:
    """
    Extracts high-specificity entity anchors from a query:
    1. Numeric tokens or tokens containing digits (e.g. 2024, 50000, CS101, 10th)
    2. Uppercase acronyms / codes in original text (e.g. BSCS, AI, MBA, MBBS, FAST, NUST)
    3. Capitalized terms (len >= 4) that are not sentence-initial common words
    """
    if not text:
        return set()

    anchors = set()
    raw_tokens = re.findall(r"\b[\w\-]+\b", text)
    for i, token in enumerate(raw_tokens):
        # 1. Alphanumerics with digits
        if any(c.isdigit() for c in token):
            anchors.add(token.lower())
            continue

        # 2. Acronyms (e.g. BSCS, CS, AI, MBA, NUST, FAST)
        if len(token) >= 2 and token.isupper() and token.lower() not in STOP_WORDS:
            anchors.add(token.lower())
            continue

        # 3. Capitalized proper entities (skip first token of sentence to avoid capitalizing generic question starters)
        if i > 0 and len(token) >= 4 and token[0].isupper() and token[1:].islower() and token.lower() not in STOP_WORDS:
            anchors.add(token.lower())

    return anchors


def has_lexical_relevance(query: str, context: str) -> bool:
    """
    Verifies that context is lexically relevant to the query with key entity anchor enforcement:
    1. If query contains specific entity anchors (e.g. BSCS, 2024, FAST), at least one MUST appear in context.
    2. General substantive content terms must meet minimum overlap ratios.
    """
    query_terms = content_terms(query)
    if not query_terms or not context.strip():
        return False

    context_terms = content_terms(context)
    overlap = query_terms & context_terms
    if not overlap:
        return False

    # Anchor Constraint: High-specificity anchors must be grounded in context
    anchors = extract_key_anchors(query)
    if anchors:
        context_raw_lower = context.lower()
        if not any(anchor in context_raw_lower for anchor in anchors):
            return False

    overlap_ratio = len(overlap) / max(len(query_terms), 1)
    if len(query_terms) <= 2:
        return len(overlap) == len(query_terms) or (anchors and bool(anchors & overlap))
    return len(overlap) >= 2 and (overlap_ratio >= 0.4 or bool(anchors & overlap))


def filter_lexically_relevant_sources(query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        source
        for source in sources
        if has_lexical_relevance(query, source.get("text", ""))
    ]


def filter_hybrid_relevant_sources(query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Semantic-first fallback with strengthened lexical anchor verification:
    - Distance <= 0.30: High-confidence semantic match (retained directly).
    - Distance between 0.30 and 0.55: Retained ONLY if key entity anchors or content terms are grounded in chunk.
    - Missing distance: Strictly requires has_lexical_relevance.
    """
    filtered = []
    query_terms = content_terms(query)
    anchors = extract_key_anchors(query)

    for src in sources:
        text = src.get("text", "")
        dist = src.get("dense_distance")
        context_terms_set = content_terms(text)

        # Entity Anchor Check: If query contains explicit anchors, chunk must ground at least one
        if anchors:
            text_lower = text.lower()
            if not any(anchor in text_lower for anchor in anchors):
                continue

        # 1. High-confidence semantic match
        if dist is not None and dist <= 0.30:
            filtered.append(src)
        # 2. Borderline semantic match (0.30 < dist <= 0.55): require lexical grounding
        elif dist is not None and dist <= settings.RERANK_FALLBACK_SIMILARITY_THRESHOLD:
            if not query_terms or bool(query_terms & context_terms_set):
                filtered.append(src)
        # 3. Lexical fallback (for sparse-only or rerank API timeouts)
        elif has_lexical_relevance(query, text):
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

