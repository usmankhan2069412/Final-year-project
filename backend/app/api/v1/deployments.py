import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant_db, get_current_org_id
from app.services.deployment import DeploymentService
from app.schemas.whatsapp import DeploymentCreate, DeploymentResponse

router = APIRouter()


@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    data: DeploymentCreate,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    try:
        return await DeploymentService.create_deployment(db=db, org_id=org_id, data=data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/details/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    deployment = await DeploymentService.get_deployment(db=db, org_id=org_id, deployment_id=deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or access denied."
        )
    return deployment


@router.get("/{chatbot_id}", response_model=List[DeploymentResponse])
async def get_deployments(
    chatbot_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    return await DeploymentService.get_deployments(db=db, org_id=org_id, chatbot_id=chatbot_id)


@router.patch("/{deployment_id}/activate", response_model=DeploymentResponse)
async def activate_deployment(
    deployment_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    deployment = await DeploymentService.activate(db=db, org_id=org_id, deployment_id=deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or access denied."
        )
    return deployment


@router.patch("/{deployment_id}/deactivate", response_model=DeploymentResponse)
async def deactivate_deployment(
    deployment_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    deployment = await DeploymentService.deactivate(db=db, org_id=org_id, deployment_id=deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or access denied."
        )
    return deployment


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(
    deployment_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    org_id: uuid.UUID = Depends(get_current_org_id)
):
    success = await DeploymentService.delete_deployment(db=db, org_id=org_id, deployment_id=deployment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or access denied."
        )
    return None
