import uuid
import json
import asyncio
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db, get_current_org_id, get_current_user_or_api_key
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.persona import Persona
from app.models.conversation import Conversation, Message, ConversationStatus, MessageRole
from app.schemas.analytics import AgentReplyRequest
from app.services.sse_manager import sse_manager

router = APIRouter()

@router.get("/conversations")
def get_escalated_conversations(
    assigned_only: bool = False,
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_api_key),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    query = db.query(Conversation).join(
        Chatbot, Chatbot.id == Conversation.chatbot_id
    ).filter(
        Chatbot.org_id == org_id,
        Conversation.status == ConversationStatus.ESCALATED,
        Conversation.deleted_at == None
    )
    if assigned_only:
        query = query.filter(Conversation.assigned_agent_id == current_user.id)
    
    conversations = query.order_by(Conversation.started_at.desc()).all()
    
    result = []
    for conv in conversations:
        chatbot_name = db.query(Persona.name).join(Chatbot, Chatbot.persona_id == Persona.id).filter(Chatbot.id == conv.chatbot_id).scalar() or "Bot"
        
        messages = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.asc()).all()
        
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
def reply_to_conversation(
    conversation_id: uuid.UUID,
    payload: AgentReplyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    conversation = db.query(Conversation).join(
        Chatbot, Chatbot.id == Conversation.chatbot_id
    ).filter(
        Conversation.id == conversation_id,
        Chatbot.org_id == org_id,
        Conversation.deleted_at == None
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or inaccessible"
        )
        
    # Check if conversation is escalated
    if conversation.status != ConversationStatus.ESCALATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation is not in escalated state"
        )

    # Insert agent reply message
    reply_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.BOT,
        content=payload.message,
        config_id=None
    )
    db.add(reply_msg)
    
    # Update chatbot stats
    chatbot = conversation.chatbot
    if chatbot:
        chatbot.total_messages += 1
        db.add(chatbot)
        
    db.commit()
    db.refresh(reply_msg)

    # If WhatsApp, execute channel client
    if conversation.deployment and conversation.deployment.channel.value == "whatsapp" and conversation.sender_phone:
        from app.services.whatsapp import WhatsAppService
        try:
            WhatsAppService.send_whatsapp_message(
                phone_number=conversation.sender_phone,
                text=payload.message,
                phone_number_id=conversation.deployment.whatsapp_phone_number_id
            )
        except Exception as e:
            # Log error but don't fail the HTTP reply
            import logging
            logging.getLogger(__name__).warning("Failed to send outbound WhatsApp reply: %s", e)

    # Broadcast agent reply message via SSE
    agent_msg_data = {
        "conversation_id": str(conversation.id),
        "message": {
            "id": str(reply_msg.id),
            "role": "bot",
            "content": payload.message,
            "created_at": reply_msg.created_at.isoformat()
        }
    }
    
    background_tasks.add_task(sse_manager.broadcast, str(org_id), "message", agent_msg_data)

    return {"status": "success", "message": agent_msg_data["message"]}


@router.post("/conversations/{conversation_id}/resolve")
def resolve_conversation(
    conversation_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    conversation = db.query(Conversation).join(
        Chatbot, Chatbot.id == Conversation.chatbot_id
    ).filter(
        Conversation.id == conversation_id,
        Chatbot.org_id == org_id,
        Conversation.deleted_at == None
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or inaccessible"
        )

    # Transition to resolved
    conversation.status = ConversationStatus.RESOLVED
    db.add(conversation)
    db.commit()

    # Broadcast resolve event via SSE
    resolve_event = {
        "conversation_id": str(conversation.id),
        "status": "resolved"
    }
    
    background_tasks.add_task(sse_manager.broadcast, str(org_id), "resolve", resolve_event)

    return {"status": "success", "conversation_id": conversation.id}


@router.get("/stream")
@router.get("/conversations/stream")
async def sse_stream(
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    async def event_generator():
        queue = await sse_manager.subscribe(str(org_id))
        try:
            while True:
                payload = await queue.get()
                event_type = payload.get("event")
                data = payload.get("data")
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        finally:
            await sse_manager.unsubscribe(str(org_id), queue)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
