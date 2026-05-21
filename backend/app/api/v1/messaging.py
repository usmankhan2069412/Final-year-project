import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.chat import ChatService
from app.db.base_repository import MessageRepository

router = APIRouter()
message_repo = MessageRepository()

@router.post("/{chatbot_id}/message", response_model=ChatResponse)
def send_message(
    chatbot_id: uuid.UUID,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message to the chatbot and get an Agentic RAG-powered response.
    Initializes a new conversation if conversation_id is omitted.
    """
    from app.models.chatbot import Chatbot
    chatbot = db.query(Chatbot).filter(Chatbot.id == chatbot_id, Chatbot.deleted_at == None).first()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
        
    try:
        result = ChatService.get_rag_response(
            db=db,
            org_id=chatbot.org_id,
            chatbot_id=chatbot_id,
            user_message=request.message,
            conversation_id=request.conversation_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # In production, use logger.exception(e)
        raise HTTPException(status_code=500, detail="An internal error occurred during chat processing.")

@router.get("/{conversation_id}/history", response_model=List[MessageResponse])
def get_chat_history(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get the message history for a specific conversation session.
    """
    from app.models.conversation import Conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id, 
        Conversation.deleted_at == None
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    start_date = conversation.started_at
    end_date = datetime.now(timezone.utc)
    
    history = message_repo.fetch_history(db, conversation_id, start_date, end_date)
    return history
