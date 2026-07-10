import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant_db, get_current_org_id
from app.services.bot import model_config_service
from app.schemas.bot import (
    AIProviderResponse,
    AIModelConfigCreate, AIModelConfigUpdate, AIModelConfigResponse
)

router = APIRouter()


@router.get("/available", response_model=List[dict])
async def get_available_models(db: AsyncSession = Depends(get_tenant_db)):
    return await model_config_service.get_available_models(db=db)


@router.get("/providers", response_model=List[AIProviderResponse])
async def get_providers(db: AsyncSession = Depends(get_tenant_db)):
    return await model_config_service.get_providers(db=db)


@router.post("/configs", response_model=AIModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_model_config(
    config_in: AIModelConfigCreate,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        return await model_config_service.create_model_config(db=db, org_id=org_id, config_in=config_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/configs", response_model=List[AIModelConfigResponse])
async def get_model_configs(
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    return await model_config_service.get_model_configs(db=db, org_id=org_id)


@router.get("/configs/{config_id}", response_model=AIModelConfigResponse)
async def get_model_config(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    config = await model_config_service.get_model_config(db=db, org_id=org_id, config_id=config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model configuration not found or access denied."
        )
    return config


@router.patch("/configs/{config_id}", response_model=AIModelConfigResponse)
async def update_model_config(
    config_id: uuid.UUID,
    config_in: AIModelConfigUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        config = await model_config_service.update_model_config(
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
async def delete_model_config(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    success = await model_config_service.delete_model_config(db=db, org_id=org_id, config_id=config_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model configuration not found or access denied."
        )
    return None
