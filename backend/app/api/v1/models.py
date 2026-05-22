import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db, get_current_org_id
from app.services.bot import model_config_service
from app.schemas.bot import (
    AIProviderResponse,
    AIModelConfigCreate, AIModelConfigUpdate, AIModelConfigResponse
)

router = APIRouter()


# --- AI Providers Endpoints ---

@router.get("/providers", response_model=List[AIProviderResponse])
def get_providers(db: Session = Depends(get_tenant_db)):
    """Retrieve available AI Providers (e.g. OpenAI, Anthropic, Gemini)."""
    return model_config_service.get_providers(db=db)


# --- AI Model Configuration Endpoints ---

@router.post("/configs", response_model=AIModelConfigResponse, status_code=status.HTTP_201_CREATED)
def create_model_config(
    config_in: AIModelConfigCreate,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Create a new AI provider configuration with optional routing rules."""
    try:
        return model_config_service.create_model_config(db=db, org_id=org_id, config_in=config_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/configs", response_model=List[AIModelConfigResponse])
def get_model_configs(
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Retrieve all configured AI providers for the active organization."""
    return model_config_service.get_model_configs(db=db, org_id=org_id)


@router.get("/configs/{config_id}", response_model=AIModelConfigResponse)
def get_model_config(
    config_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Retrieve details of a specific AI configuration."""
    config = model_config_service.get_model_config(db=db, org_id=org_id, config_id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model configuration not found or access denied."
        )
    return config


@router.patch("/configs/{config_id}", response_model=AIModelConfigResponse)
def update_model_config(
    config_id: uuid.UUID,
    config_in: AIModelConfigUpdate,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Update details of an existing AI provider configuration and/or update routing rules."""
    try:
        config = model_config_service.update_model_config(
            db=db, org_id=org_id, config_id=config_id, config_in=config_in
        )
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI model configuration not found or access denied."
            )
        return config
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_config(
    config_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    """Delete an existing AI provider configuration and all its routing rules."""
    success = model_config_service.delete_model_config(db=db, org_id=org_id, config_id=config_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model configuration not found or access denied."
        )
    return None
