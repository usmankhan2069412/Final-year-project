import uuid
import logging
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
import json
from app.services.sse_manager import sse_manager
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_tenant_db, get_current_org_id
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.chat import ChatService
from app.db.base_repository import MessageRepository
from app.models.conversation import Deployment, Conversation
from app.models.chatbot import Chatbot

router = APIRouter()
message_repo = MessageRepository()

@router.post("/{chatbot_id}/message")
def send_message(
    chatbot_id: uuid.UUID,
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    stream: bool = False,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    """
    Send a message to the chatbot and get an Agentic RAG-powered response.
    Initializes a new conversation if conversation_id is omitted.
    """
    chatbot = db.query(Chatbot).filter(
        Chatbot.id == chatbot_id,
        Chatbot.org_id == org_id,
        Chatbot.deleted_at == None
    ).first()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
        
    try:
        if stream:
            return StreamingResponse(
                ChatService.get_rag_stream(
                    db=db,
                    org_id=org_id,
                    chatbot_id=chatbot_id,
                    user_message=request.message,
                    conversation_id=request.conversation_id,
                    background_tasks=background_tasks
                ),
                media_type="text/event-stream"
            )
            
        result = ChatService.get_rag_response(
            db=db,
            org_id=org_id,
            chatbot_id=chatbot_id,
            user_message=request.message,
            conversation_id=request.conversation_id,
            background_tasks=background_tasks
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("[CHAT 500] Unhandled exception in send_message: %s", e)
        raise HTTPException(status_code=500, detail="An internal error occurred during chat processing.")

@router.get("/{conversation_id}/history", response_model=List[MessageResponse])
def get_chat_history(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    """
    Get the message history for a specific conversation session.
    """
    conversation = db.query(Conversation).join(Chatbot, Conversation.chatbot_id == Chatbot.id).filter(
        Conversation.id == conversation_id,
        Chatbot.org_id == org_id,
        Conversation.deleted_at == None,
        Chatbot.deleted_at == None,
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    start_date = conversation.started_at
    end_date = datetime.now(timezone.utc)
    
    history = message_repo.fetch_history(db, conversation_id, start_date, end_date)
    return history


@router.post("/public/deployments/{deployment_id}/message")
def send_public_deployment_message(
    deployment_id: uuid.UUID,
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    stream: bool = False,
    db: Session = Depends(get_db),
):
    """Public web-widget runtime endpoint scoped by an active deployment id."""
    deployment = db.query(Deployment).join(Chatbot, Deployment.chatbot_id == Chatbot.id).filter(
        Deployment.id == deployment_id,
        Deployment.is_active == True,
        Chatbot.deleted_at == None,
    ).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active deployment not found")

    chatbot = deployment.chatbot
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    try:
        if stream:
            return StreamingResponse(
                ChatService.get_rag_stream(
                    db=db,
                    org_id=chatbot.org_id,
                    chatbot_id=chatbot.id,
                    user_message=request.message,
                    conversation_id=request.conversation_id,
                    deployment_id=deployment.id,
                    background_tasks=background_tasks,
                ),
                media_type="text/event-stream"
            )
            
        return ChatService.get_rag_response(
            db=db,
            org_id=chatbot.org_id,
            chatbot_id=chatbot.id,
            user_message=request.message,
            conversation_id=request.conversation_id,
            deployment_id=deployment.id,
            background_tasks=background_tasks
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred during chat processing.")

@router.get("/{chatbot_id}/conversations/{conversation_id}/stream")
async def builder_sse_stream(
    chatbot_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    """Authenticated SSE stream for the builder/test chat interface."""
    chatbot = db.query(Chatbot).filter(
        Chatbot.id == chatbot_id,
        Chatbot.org_id == org_id,
        Chatbot.deleted_at == None
    ).first()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found or inaccessible")
        
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.chatbot_id == chatbot_id,
        Conversation.deleted_at == None
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    async def event_generator():
        channel = f"conversation:{conversation_id}"
        queue = await sse_manager.subscribe(channel)
        try:
            while True:
                payload = await queue.get()
                event_type = payload.get("event")
                data = payload.get("data")
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        finally:
            await sse_manager.unsubscribe(channel, queue)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/public/deployments/{deployment_id}/conversations/{conversation_id}/stream")
async def public_sse_stream(
    deployment_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Public SSE stream for deployed widgets."""
    deployment = db.query(Deployment).join(Chatbot, Deployment.chatbot_id == Chatbot.id).filter(
        Deployment.id == deployment_id,
        Deployment.is_active == True,
        Chatbot.deleted_at == None,
    ).first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Active deployment not found")
        
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.chatbot_id == deployment.chatbot_id,
        Conversation.deleted_at == None
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    async def event_generator():
        channel = f"conversation:{conversation_id}"
        queue = await sse_manager.subscribe(channel)
        try:
            while True:
                payload = await queue.get()
                event_type = payload.get("event")
                data = payload.get("data")
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        finally:
            await sse_manager.unsubscribe(channel, queue)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
