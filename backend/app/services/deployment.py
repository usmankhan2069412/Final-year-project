import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.chatbot import Chatbot
from app.models.conversation import Deployment, Channel
from app.schemas.whatsapp import DeploymentCreate

class DeploymentService:

    @staticmethod
    def create_deployment(db: Session, org_id: uuid.UUID, data: DeploymentCreate) -> Deployment:
        """Create a new deployment for a chatbot in the tenant organization."""
        # Validate chatbot exists and belongs to the tenant org
        chatbot = db.query(Chatbot).filter(
            Chatbot.id == data.chatbot_id,
            Chatbot.org_id == org_id,
            Chatbot.deleted_at == None
        ).first()
        
        if not chatbot:
            raise ValueError("Chatbot not found or inaccessible")
            
        if data.channel == Channel.WHATSAPP and not data.whatsapp_phone_number_id:
            raise ValueError("WhatsApp Phone Number ID is required for WhatsApp deployments")
            
        deployment = Deployment(
            chatbot_id=data.chatbot_id,
            channel=data.channel,
            whatsapp_phone_number_id=data.whatsapp_phone_number_id,
            whatsapp_business_account_id=data.whatsapp_business_account_id,
            is_active=False
        )
        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        return deployment

    @staticmethod
    def get_deployments(db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID) -> List[Deployment]:
        """List all deployments for a chatbot inside the tenant organization."""
        return (
            db.query(Deployment)
            .join(Chatbot, Deployment.chatbot_id == Chatbot.id)
            .filter(
                Deployment.chatbot_id == chatbot_id,
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
            .all()
        )

    @staticmethod
    def get_deployment(db: Session, org_id: uuid.UUID, deployment_id: uuid.UUID) -> Optional[Deployment]:
        """Get a specific deployment inside the tenant organization."""
        return (
            db.query(Deployment)
            .join(Chatbot, Deployment.chatbot_id == Chatbot.id)
            .filter(
                Deployment.id == deployment_id,
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
            .first()
        )

    @staticmethod
    def activate(db: Session, org_id: uuid.UUID, deployment_id: uuid.UUID) -> Optional[Deployment]:
        """Activate a deployment."""
        deployment = DeploymentService.get_deployment(db, org_id, deployment_id)
        if not deployment:
            return None
            
        deployment.is_active = True
        db.commit()
        db.refresh(deployment)
        return deployment

    @staticmethod
    def deactivate(db: Session, org_id: uuid.UUID, deployment_id: uuid.UUID) -> Optional[Deployment]:
        """Deactivate a deployment."""
        deployment = DeploymentService.get_deployment(db, org_id, deployment_id)
        if not deployment:
            return None
            
        deployment.is_active = False
        db.commit()
        db.refresh(deployment)
        return deployment

    @staticmethod
    def delete_deployment(db: Session, org_id: uuid.UUID, deployment_id: uuid.UUID) -> bool:
        """Delete a deployment."""
        deployment = DeploymentService.get_deployment(db, org_id, deployment_id)
        if not deployment:
            return False
            
        db.delete(deployment)
        db.commit()
        return True

    @staticmethod
    def get_by_phone_number_id(db: Session, phone_number_id: str) -> Optional[Deployment]:
        """Route inbound webhook to deployment, eagerly loading the chatbot info."""
        return (
            db.query(Deployment)
            .filter(
                Deployment.whatsapp_phone_number_id == phone_number_id,
                Deployment.is_active == True
            )
            .first()
        )
