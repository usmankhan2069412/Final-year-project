import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db
from app.services.deployment import DeploymentService
from app.schemas.whatsapp import DeploymentCreate, DeploymentResponse

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


@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
def create_deployment(data: DeploymentCreate, db: Session = Depends(get_tenant_db)):
    """Create a new deployment for a chatbot."""
    org_id = _get_org_id(db)
    try:
        return DeploymentService.create_deployment(db=db, org_id=org_id, data=data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{chatbot_id}", response_model=List[DeploymentResponse])
def get_deployments(chatbot_id: uuid.UUID, db: Session = Depends(get_tenant_db)):
    """List all deployments for a chatbot."""
    org_id = _get_org_id(db)
    return DeploymentService.get_deployments(db=db, org_id=org_id, chatbot_id=chatbot_id)


@router.get("/details/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(deployment_id: uuid.UUID, db: Session = Depends(get_tenant_db)):
    """Retrieve details of a specific deployment."""
    org_id = _get_org_id(db)
    deployment = DeploymentService.get_deployment(db=db, org_id=org_id, deployment_id=deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or access denied."
        )
    return deployment


@router.patch("/{deployment_id}/activate", response_model=DeploymentResponse)
def activate_deployment(deployment_id: uuid.UUID, db: Session = Depends(get_tenant_db)):
    """Activate a deployment."""
    org_id = _get_org_id(db)
    deployment = DeploymentService.activate(db=db, org_id=org_id, deployment_id=deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or access denied."
        )
    return deployment


@router.patch("/{deployment_id}/deactivate", response_model=DeploymentResponse)
def deactivate_deployment(deployment_id: uuid.UUID, db: Session = Depends(get_tenant_db)):
    """Deactivate a deployment."""
    org_id = _get_org_id(db)
    deployment = DeploymentService.deactivate(db=db, org_id=org_id, deployment_id=deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or access denied."
        )
    return deployment


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deployment(deployment_id: uuid.UUID, db: Session = Depends(get_tenant_db)):
    """Delete a deployment configuration."""
    org_id = _get_org_id(db)
    success = DeploymentService.delete_deployment(db=db, org_id=org_id, deployment_id=deployment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or access denied."
        )
    return None
