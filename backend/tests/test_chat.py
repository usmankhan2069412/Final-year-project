import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.chat import ChatService
from app.models.conversation import ConversationStatus

client = TestClient(app)

@patch("app.api.v1.messaging.ChatService.get_rag_response")
def test_send_message_endpoint(mock_get_rag_response):
    """
    Test the Chat endpoint successfully returns the RAG response.
    """
    mock_get_rag_response.return_value = {
        "response": "Hello, how can I help?",
        "conversation_id": "00000000-0000-0000-0000-000000000001",
        "sources": [],
        "status": ConversationStatus.ONGOING
    }
    
    from app.api.deps import get_tenant_db, get_current_org_id

    org_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    mock_db = MagicMock()
    mock_chatbot = MagicMock()
    mock_chatbot.org_id = org_id
    mock_db.query.return_value.filter.return_value.first.return_value = mock_chatbot

    def override_get_tenant_db():
        yield mock_db

    def override_get_current_org_id():
        return org_id

    app.dependency_overrides[get_tenant_db] = override_get_tenant_db
    app.dependency_overrides[get_current_org_id] = override_get_current_org_id
        
    response = client.post(
        "/api/v1/chat/00000000-0000-0000-0000-000000000002/message",
        json={"message": "Hi"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Hello, how can I help?"
    assert data["status"] == ConversationStatus.ONGOING.value
        
    app.dependency_overrides.clear()


def test_agent_intent_routing():
    """
    Unit test for the intent router classification heuristics without LLM.
    """
    # 1. Handoff keyword
    state = {"user_message": "talk to human", "api_key": None}
    res = ChatService.route_intent(state)
    assert res["intent"] == "AGENT_HANDOFF"
    
    # 2. Conversational keyword
    state = {"user_message": "hello", "api_key": None}
    res = ChatService.route_intent(state)
    assert res["intent"] == "CONVERSATIONAL"
    
    # 3. RAG Lookup (no keywords match)
    state = {"user_message": "what is your pricing?", "api_key": None}
    res = ChatService.route_intent(state)
    assert res["intent"] == "RAG_LOOKUP"
