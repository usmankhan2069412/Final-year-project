import pytest

from app.services.chat import AgentGraphExecutor
from app.services.chunker import TextChunker


def test_chunker_prefers_sentence_boundaries_and_overlap():
    text = (
        "Pricing starts at ten dollars per month for the starter plan. "
        "Enterprise customers can request custom onboarding and support. "
        "Refunds are available within fourteen days when usage is low."
    )

    chunks = TextChunker.split_text(text, chunk_size=80, overlap=12)

    assert len(chunks) >= 2
    assert all(len(chunk) <= 80 for chunk in chunks)
    assert chunks[0].endswith(".")
    assert "Enterprise customers" in " ".join(chunks)


def test_chunker_rejects_invalid_overlap():
    with pytest.raises(ValueError, match="overlap must be smaller"):
        TextChunker.split_text("hello world", chunk_size=10, overlap=10)


def test_no_llm_relevance_validation_rejects_unrelated_context():
    state = {
        "api_key": None,
        "user_message": "What are the pricing plans?",
        "rewritten_query": "pricing plans",
        "context_text": "Office hours are Monday to Friday from nine to five.",
    }

    assert AgentGraphExecutor.validate_node(state)["is_relevant"] is False


def test_no_llm_relevance_validation_accepts_related_context():
    state = {
        "api_key": None,
        "user_message": "What are the pricing plans?",
        "rewritten_query": "pricing plans",
        "context_text": "Pricing plans include starter, growth, and enterprise tiers.",
    }

    assert AgentGraphExecutor.validate_node(state)["is_relevant"] is True
