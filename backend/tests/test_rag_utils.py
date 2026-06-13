import pytest
from types import SimpleNamespace

from app.services.chat import AgentGraphExecutor
from app.services.semantic_router import SemanticRouter
from app.services.chunker import TextChunker
from app.models.document import KnowledgeSource, SourceType
from app.models.conversation import MessageRole


def test_chunker_prefers_sentence_boundaries_and_overlap():
    text = (
        "Pricing starts at ten dollars per month for the starter plan. "
        "Enterprise customers can request custom onboarding and support. "
        "Refunds are available within fourteen days when usage is low."
    )

    chunks = TextChunker.split_text(text, chunk_size=80, overlap=12)

    assert len(chunks) >= 1
    # Because chunk_size is now token-based, lengths can be up to ~320 characters
    assert all(len(chunk) <= 320 for chunk in chunks)
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
        "sources": [
            {
                "chunk_id": "office-hours",
                "source_id": "source-1",
                "text": "Office hours are Monday to Friday from nine to five.",
                "score": 1.0,
            }
        ],
    }

    assert AgentGraphExecutor.validate_node(state)["is_relevant"] is False


def test_no_llm_relevance_validation_accepts_related_context():
    state = {
        "api_key": None,
        "user_message": "What are the pricing plans?",
        "rewritten_query": "pricing plans",
        "context_text": "Pricing plans include starter, growth, and enterprise tiers.",
        "sources": [
            {
                "chunk_id": "pricing",
                "source_id": "source-1",
                "text": "Pricing plans include starter, growth, and enterprise tiers.",
                "score": 1.0,
            }
        ],
    }

    assert AgentGraphExecutor.validate_node(state)["is_relevant"] is True


def test_no_llm_relevance_validation_drops_only_unrelated_chunks():
    state = {
        "api_key": None,
        "user_message": "What are the refund rules?",
        "rewritten_query": "refund rules",
        "context_text": (
            "[Source 1]\nRefund rules allow returns within fourteen days.\n\n"
            "[Source 2]\nOffice hours are Monday to Friday from nine to five."
        ),
        "sources": [
            {
                "chunk_id": "refund",
                "source_id": "source-1",
                "text": "Refund rules allow returns within fourteen days.",
                "score": 1.0,
            },
            {
                "chunk_id": "office-hours",
                "source_id": "source-2",
                "text": "Office hours are Monday to Friday from nine to five.",
                "score": 0.9,
            },
        ],
    }

    result = AgentGraphExecutor.validate_node(state)

    assert result["is_relevant"] is True
    assert [source["chunk_id"] for source in result["sources"]] == ["refund"]
    assert "Office hours" not in result["context_text"]


def test_source_searchability_marks_metadata_as_handoff_only():
    searchable = KnowledgeSource(source_type=SourceType.TEXT)
    handoff_only = KnowledgeSource(source_type=SourceType.PHONE)

    assert searchable.is_searchable is True
    assert handoff_only.is_searchable is False


def test_history_transform_fast_path_detects_follow_up_requests():
    assert SemanticRouter._matches_history_transform("translate them into roman urdu") is True
    assert SemanticRouter._matches_history_transform("make it shorter") is True
    assert SemanticRouter._matches_history_transform("summarize above") is True
    assert SemanticRouter._matches_history_transform("tell me about pricing") is False


def test_history_transform_node_uses_full_last_bot_answer(monkeypatch):
    roadmap = (
        "Python Mastery\n"
        "System Design Basics\n"
        "Databases\n"
        "LLM Internals\n"
        "RAG Mastery\n"
        "AI Evaluation Systems"
    )
    captured = {}

    class FakeLLM:
        def invoke(self, messages):
            captured["prompt"] = messages[-1].content
            return SimpleNamespace(content="Roman Urdu roadmap")

    monkeypatch.setattr(
        AgentGraphExecutor,
        "_get_llm",
        staticmethod(lambda state, temperature=0.3: FakeLLM()),
    )

    state = {
        "user_message": "translate them into roman urdu",
        "history": [
            SimpleNamespace(role=MessageRole.USER, content="give me the roadmap of agentic ai"),
            SimpleNamespace(role=MessageRole.BOT, content=roadmap),
        ],
        "persona": SimpleNamespace(name="Aina"),
        "traits": ["Friendly"],
        "api_key": "test-key",
    }

    result = AgentGraphExecutor.history_transform_node(state)

    assert result["response"] == "Roman Urdu roadmap"
    assert result["response_source"] == "history_transform"
    assert result["sources"] == []
    assert "Python Mastery" in captured["prompt"]
    assert "AI Evaluation Systems" in captured["prompt"]


def test_history_transform_node_asks_for_text_when_history_missing():
    state = {
        "user_message": "translate them into roman urdu",
        "history": [],
        "persona": SimpleNamespace(name="Aina"),
        "traits": [],
        "api_key": None,
    }

    result = AgentGraphExecutor.history_transform_node(state)

    assert result["response_source"] == "history_transform"
    assert result["sources"] == []
    assert "text" in result["response"].lower()
