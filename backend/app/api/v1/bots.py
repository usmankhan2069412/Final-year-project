import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db
from app.services.bot import bot_service
from app.schemas.bot import (
    PersonaCreate, PersonaUpdate, PersonaResponse,
    ChatbotCreate, ChatbotUpdate, ChatbotResponse
)

router = APIRouter()


def _get_org_id(db: Session) -> uuid.UUID:
    """Helper to retrieve the resolved organization ID from the db session context."""
    org_id_str = db.execute(text("SELECT current_setting('app.current_org_id', true)")).scalar()
    if not org_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is missing."
        )
    try:
        return uuid.UUID(org_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format in tenant context."
        )


# --- Personas Endpoints ---

@router.post("/personas", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
def create_persona(persona_in: PersonaCreate, db: Session = Depends(get_tenant_db)):
    """Create a custom persona for the active organization."""
    org_id = _get_org_id(db)
    return bot_service.create_persona(db=db, org_id=org_id, persona_in=persona_in)


@router.get("/personas", response_model=List[PersonaResponse])
def get_personas(db: Session = Depends(get_tenant_db)):
    """Retrieve custom personas for the organization along with built-in system personas."""
    org_id = _get_org_id(db)
    return bot_service.get_personas(db=db, org_id=org_id)


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
def get_persona(persona_id: uuid.UUID, db: Session = Depends(get_tenant_db)):
    """Retrieve details of a specific custom or system persona."""
    org_id = _get_org_id(db)
    persona = bot_service.get_persona(db=db, org_id=org_id, persona_id=persona_id)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found or access denied."
        )
    return persona


@router.patch("/personas/{persona_id}", response_model=PersonaResponse)
def update_persona(persona_id: uuid.UUID, persona_in: PersonaUpdate, db: Session = Depends(get_tenant_db)):
    """Update a custom persona configuration."""
    org_id = _get_org_id(db)
    persona = bot_service.update_persona(
        db=db, org_id=org_id, persona_id=persona_id, persona_in=persona_in
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found, access denied, or system personas cannot be updated."
        )
    return persona


@router.delete("/personas/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persona(persona_id: uuid.UUID, db: Session = Depends(get_tenant_db)):
    """Soft delete a custom persona."""
    org_id = _get_org_id(db)
    success = bot_service.delete_persona(db=db, org_id=org_id, persona_id=persona_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found or access denied."
        )
    return None


# --- Chatbots Endpoints ---

@router.post("/chatbots", response_model=ChatbotResponse, status_code=status.HTTP_201_CREATED)
def create_chatbot(chatbot_in: ChatbotCreate, db: Session = Depends(get_tenant_db)):
    """Create a new chatbot instance associated with an accessible persona."""
    org_id = _get_org_id(db)
    try:
        return bot_service.create_chatbot(db=db, org_id=org_id, chatbot_in=chatbot_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/chatbots", response_model=List[ChatbotResponse])
def get_chatbots(db: Session = Depends(get_tenant_db)):
    """Retrieve all active chatbot definitions for the organization."""
    org_id = _get_org_id(db)
    return bot_service.get_chatbots(db=db, org_id=org_id)


@router.get("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
def get_chatbot(chatbot_id: uuid.UUID, db: Session = Depends(get_tenant_db)):
    """Retrieve a specific chatbot configuration."""
    org_id = _get_org_id(db)
    chatbot = bot_service.get_chatbot(db=db, org_id=org_id, chatbot_id=chatbot_id)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found or access denied."
        )
    return chatbot


@router.patch("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
def update_chatbot(chatbot_id: uuid.UUID, chatbot_in: ChatbotUpdate, db: Session = Depends(get_tenant_db)):
    """Update settings of an existing chatbot."""
    org_id = _get_org_id(db)
    try:
        chatbot = bot_service.update_chatbot(
            db=db, org_id=org_id, chatbot_id=chatbot_id, chatbot_in=chatbot_in
        )
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found or access denied."
            )
        return chatbot
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/chatbots/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chatbot(chatbot_id: uuid.UUID, db: Session = Depends(get_tenant_db)):
    """Soft delete a chatbot configuration."""
    org_id = _get_org_id(db)
    success = bot_service.delete_chatbot(db=db, org_id=org_id, chatbot_id=chatbot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found or access denied."
        )
    return None
