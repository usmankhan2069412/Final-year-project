import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.conversation import ConversationStatus, Message as DBMessage
from app.services.escalation_router import EscalationRouter


def test_escalation_broadcasts_distinct_message_ids(monkeypatch):
    org_id = uuid.uuid4()
    assigned_agent_id = uuid.uuid4()
    conversation = SimpleNamespace(
        id=uuid.uuid4(),
        status=ConversationStatus.ONGOING,
        assigned_agent_id=None,
    )
    chatbot = SimpleNamespace(
        id=uuid.uuid4(),
        total_messages=0,
        total_conversations=0,
    )
    db = MagicMock()
    events = []

    monkeypatch.setattr(EscalationRouter, "find_least_busy_agent", lambda *_args: assigned_agent_id)

    async def fake_broadcast(channel, event_type, data):
        events.append((channel, event_type, data))

    monkeypatch.setattr("app.services.sse_manager.sse_manager.broadcast", fake_broadcast)

    async def run_escalation():
        result = EscalationRouter.escalate(
            db=db,
            conversation=conversation,
            chatbot=chatbot,
            org_id=org_id,
            user_message="I need a human",
            response_text="A support agent is reviewing your message and will respond shortly.",
            language="english",
            is_new_conv=True,
        )
        await asyncio.sleep(0)
        return result

    result = asyncio.run(run_escalation())

    assert result["status"] == ConversationStatus.ESCALATED
    assert conversation.assigned_agent_id == assigned_agent_id
    assert chatbot.total_messages == 2
    assert chatbot.total_conversations == 1
    assert db.commit.call_count == 1

    saved_messages = [call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], DBMessage)]
    assert len(saved_messages) == 2
    assert saved_messages[0].id != saved_messages[1].id

    message_events = [data for _channel, event_type, data in events if event_type == "message"]
    assert len(message_events) == 2
    assert message_events[0]["message"]["id"] != message_events[1]["message"]["id"]
    assert all(event["message"]["created_at"] for event in message_events)


def test_escalated_bypass_broadcasts_distinct_message_ids(monkeypatch):
    org_id = uuid.uuid4()
    conversation = SimpleNamespace(id=uuid.uuid4())
    chatbot = SimpleNamespace(id=uuid.uuid4(), total_messages=0)
    db = MagicMock()
    events = []

    async def fake_broadcast(channel, event_type, data):
        events.append((channel, event_type, data))

    monkeypatch.setattr("app.services.sse_manager.sse_manager.broadcast", fake_broadcast)

    async def run_bypass():
        result = EscalationRouter.handle_escalated_message(
            db=db,
            conversation=conversation,
            chatbot=chatbot,
            org_id=org_id,
            user_message="Are you there?",
            language="english",
        )
        await asyncio.sleep(0)
        return result

    result = asyncio.run(run_bypass())

    assert result["status"] == ConversationStatus.ESCALATED
    assert chatbot.total_messages == 2
    assert db.commit.call_count == 1

    message_events = [data for _channel, event_type, data in events if event_type == "message"]
    assert len(message_events) == 2
    assert message_events[0]["message"]["id"] != message_events[1]["message"]["id"]
