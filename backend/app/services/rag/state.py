from typing import List, Dict, Any, Optional, TypedDict
from app.models.conversation import Message as DBMessage, ConversationStatus
from app.models.persona import Persona

class AgentState(TypedDict, total=False):
    user_message: str
    history: List[DBMessage]
    api_key: Optional[str]
    model_name: str
    persona: Persona
    traits: List[str]
    chatbot_id: str

    # Pipeline variables
    intent: Optional[str]
    intent_confidence: Optional[float]
    intent_probabilities: Optional[Dict[str, float]]
    intent_method: Optional[str]
    needs_rewrite: Optional[bool]
    needs_rewrite_confidence: Optional[float]
    rewritten_query: Optional[str]
    query_vector: Optional[List[float]]
    original_query_vector: Optional[List[float]]
    rewritten_query_vector: Optional[List[float]]
    sources: List[Dict[str, Any]]
    context_text: str
    is_relevant: bool
    routing_rules: Dict[str, str]
    default_model: str

    # Semantic Cache tracking
    org_id: str
    knowledge_base_version: int
    persona_version: int
    cache_hit: bool
    cache_similarity: float
    validated_chunks_count: int

    # Conversation Memory
    conversation_memory: Optional[dict]

    # Final Output
    response: str
    response_source: str
    status: ConversationStatus
    callbacks: Optional[List[Any]]
    status_queue: Optional[Any]

    # In-Memory Seam Adapter
    retriever: Optional[Any]

