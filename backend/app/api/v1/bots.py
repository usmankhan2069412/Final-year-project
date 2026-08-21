import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant_db, get_current_org_id
from app.services.bot import bot_service
from app.schemas.bot import (
    PersonaCreate, PersonaUpdate, PersonaResponse,
    ChatbotCreate, ChatbotUpdate, ChatbotResponse
)

router = APIRouter()


@router.post("/personas", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    persona_in: PersonaCreate,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        return await bot_service.create_persona(db=db, org_id=org_id, persona_in=persona_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create persona."
        )


@router.get("/personas", response_model=List[PersonaResponse])
async def get_personas(
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        return await bot_service.get_personas(db=db, org_id=org_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch personas."
        )


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        persona = await bot_service.get_persona(db=db, org_id=org_id, persona_id=persona_id)
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found or access denied."
            )
        return persona
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch persona."
        )


@router.patch("/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: uuid.UUID,
    persona_in: PersonaUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        persona = await bot_service.update_persona(
            db=db, org_id=org_id, persona_id=persona_id, persona_in=persona_in
        )
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found, access denied, or system personas cannot be updated."
            )
        return persona
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update persona."
        )


@router.delete("/personas/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        success = await bot_service.delete_persona(db=db, org_id=org_id, persona_id=persona_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found or access denied."
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete persona."
        )


@router.post("/chatbots", response_model=ChatbotResponse, status_code=status.HTTP_201_CREATED)
async def create_chatbot(
    chatbot_in: ChatbotCreate,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        return await bot_service.create_chatbot(db=db, org_id=org_id, chatbot_in=chatbot_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/chatbots", response_model=List[ChatbotResponse])
async def get_chatbots(
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    return await bot_service.get_chatbots(db=db, org_id=org_id)


@router.get("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    chatbot = await bot_service.get_chatbot(db=db, org_id=org_id, chatbot_id=chatbot_id)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found or access denied."
        )
    return chatbot


@router.patch("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: uuid.UUID,
    chatbot_in: ChatbotUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        chatbot = await bot_service.update_chatbot(
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
async def delete_chatbot(
    chatbot_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    success = await bot_service.delete_chatbot(db=db, org_id=org_id, chatbot_id=chatbot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found or access denied."
        )
    return None
