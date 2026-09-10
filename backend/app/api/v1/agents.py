import uuid
import json
import asyncio
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.api.deps import get_tenant_db, get_current_org_id, get_current_user_or_api_key
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.persona import Persona
from app.models.conversation import Conversation, Message, ConversationStatus, MessageRole, Channel
from app.schemas.analytics import AgentReplyRequest
from app.services.sse_manager import sse_manager
from app.services.outbox import OutboxService

router = APIRouter()


@router.get("/conversations")
async def get_escalated_conversations(
    assigned_only: bool = False,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_api_key),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    stmt = (
        select(Conversation)
        .join(Chatbot, Chatbot.id == Conversation.chatbot_id)
        .where(
            Chatbot.org_id == org_id,
            Conversation.status == ConversationStatus.ESCALATED,
            Conversation.deleted_at == None
        )
    )
    if assigned_only:
        stmt = stmt.where(Conversation.assigned_agent_id == current_user.id)

    stmt = stmt.order_by(Conversation.started_at.desc())
    result = await db.execute(stmt)
    conversations = list(result.scalars().all())

    result = []
    for conv in conversations:
        persona_name_result = await db.execute(
            select(Persona.name)
            .join(Chatbot, Chatbot.persona_id == Persona.id)
            .where(Chatbot.id == conv.chatbot_id)
        )
        chatbot_name = persona_name_result.scalar() or "Bot"

        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
        )
        messages = list(msg_result.scalars().all())

        msg_list = [
            {
                "id": str(m.id),
                "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]

        last_msg = msg_list[-1]["content"] if msg_list else ""

        result.append({
            "id": str(conv.id),
            "chatbot_id": str(conv.chatbot_id),
            "chatbot_name": chatbot_name,
            "assigned_agent_id": str(conv.assigned_agent_id) if conv.assigned_agent_id else None,
            "status": conv.status.value if hasattr(conv.status, "value") else str(conv.status),
            "started_at": conv.started_at.isoformat(),
            "messages": msg_list,
            "last_message": last_msg
        })

    return result


@router.post("/conversations/{conversation_id}/reply")
async def reply_to_conversation(
    conversation_id: uuid.UUID,
    payload: AgentReplyRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    stmt = (
        select(Conversation)
        .options(
            joinedload(Conversation.chatbot),
            joinedload(Conversation.deployment)
        )
        .where(
            Conversation.id == conversation_id,
            Conversation.deleted_at == None
        )
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation or (conversation.chatbot and conversation.chatbot.org_id != org_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or inaccessible"
        )

    if conversation.status != ConversationStatus.ESCALATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation is not in escalated state"
        )

    msg_id = uuid.uuid4()
    msg_created_at = datetime.now(timezone.utc)
    reply_msg = Message(
        id=msg_id,
        conversation_id=conversation.id,
        role=MessageRole.BOT,
        content=payload.message,
        config_id=None,
        created_at=msg_created_at,
    )
    db.add(reply_msg)

    chatbot = conversation.chatbot
    if chatbot:
        await db.execute(
            update(Chatbot)
            .where(Chatbot.id == chatbot.id)
            .values({Chatbot.total_messages: Chatbot.total_messages + 1})
        )

    if conversation.deployment and conversation.deployment.channel == Channel.WHATSAPP and conversation.sender_phone:
        await OutboxService.enqueue(
            db=db,
            conversation_id=conversation.id,
            channel="whatsapp",
            payload={
                "phone_number": conversation.sender_phone,
                "text": payload.message,
                "phone_number_id": conversation.deployment.whatsapp_phone_number_id,
            },
        )

    await db.commit()

    agent_msg_data = {
        "conversation_id": str(conversation.id),
        "message": {
            "id": str(msg_id),
            "role": "bot",
            "content": payload.message,
            "created_at": msg_created_at.isoformat()
        }
    }

    # Broadcast immediately to both channels without waiting for HTTP response completion:
    asyncio.create_task(sse_manager.broadcast(f"organization:{org_id}", "message", agent_msg_data))
    asyncio.create_task(sse_manager.broadcast(f"conversation:{conversation.id}", "message", agent_msg_data))

    return {"status": "success", "message": agent_msg_data["message"]}


@router.post("/conversations/{conversation_id}/resolve")
async def resolve_conversation(
    conversation_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    stmt = (
        select(Conversation)
        .join(Chatbot, Chatbot.id == Conversation.chatbot_id)
        .where(
            Conversation.id == conversation_id,
            Chatbot.org_id == org_id,
            Conversation.deleted_at == None
        )
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or inaccessible"
        )

    conversation.status = ConversationStatus.RESOLVED
    db.add(conversation)
    await db.commit()

    resolve_event = {
        "conversation_id": str(conversation.id),
        "status": "resolved"
    }

    asyncio.create_task(sse_manager.broadcast(f"organization:{org_id}", "resolve", resolve_event))
    asyncio.create_task(sse_manager.broadcast(f"conversation:{conversation.id}", "resolve", resolve_event))

    return {"status": "success", "conversation_id": conversation.id}


@router.get("/stream")
@router.get("/conversations/stream")
async def sse_stream(
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    async def event_generator():
        queue = await sse_manager.subscribe(f"organization:{org_id}")
        try:
            while True:
                payload = await queue.get()
                event_type = payload.get("event")
                data = payload.get("data")
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        finally:
            await sse_manager.unsubscribe(f"organization:{org_id}", queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
