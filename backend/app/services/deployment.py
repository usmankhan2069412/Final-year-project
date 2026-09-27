import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.chatbot import Chatbot, ChatbotStatus
from app.models.conversation import Deployment, Channel
from app.schemas.whatsapp import DeploymentCreate


class DeploymentService:

    @staticmethod
    async def create_deployment(db: AsyncSession, org_id: uuid.UUID, data: DeploymentCreate) -> Deployment:
        result = await db.execute(
            select(Chatbot).where(
                Chatbot.id == data.chatbot_id,
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
        )
        chatbot = result.scalar_one_or_none()

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
        await db.commit()
        await db.refresh(deployment)
        return deployment

    @staticmethod
    async def get_deployments(db: AsyncSession, org_id: uuid.UUID, chatbot_id: uuid.UUID) -> List[Deployment]:
        stmt = (
            select(Deployment)
            .options(selectinload(Deployment.chatbot))
            .join(Chatbot, Deployment.chatbot_id == Chatbot.id)
            .where(
                Deployment.chatbot_id == chatbot_id,
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_deployment(db: AsyncSession, org_id: uuid.UUID, deployment_id: uuid.UUID) -> Optional[Deployment]:
        stmt = (
            select(Deployment)
            .options(selectinload(Deployment.chatbot))
            .join(Chatbot, Deployment.chatbot_id == Chatbot.id)
            .where(
                Deployment.id == deployment_id,
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def activate(db: AsyncSession, org_id: uuid.UUID, deployment_id: uuid.UUID) -> Optional[Deployment]:
        deployment = await DeploymentService.get_deployment(db, org_id, deployment_id)
        if not deployment:
            return None

        deployment.is_active = True
        if deployment.chatbot:
            deployment.chatbot.status = ChatbotStatus.ACTIVE
        await db.commit()
        await db.refresh(deployment)
        return deployment

    @staticmethod
    async def deactivate(db: AsyncSession, org_id: uuid.UUID, deployment_id: uuid.UUID) -> Optional[Deployment]:
        deployment = await DeploymentService.get_deployment(db, org_id, deployment_id)
        if not deployment:
            return None

        deployment.is_active = False
        await db.commit()
        await db.refresh(deployment)
        return deployment

    @staticmethod
    async def delete_deployment(db: AsyncSession, org_id: uuid.UUID, deployment_id: uuid.UUID) -> bool:
        deployment = await DeploymentService.get_deployment(db, org_id, deployment_id)
        if not deployment:
            return False

        await db.delete(deployment)
        await db.commit()
        return True

    @staticmethod
    def get_by_phone_number_id(db, phone_number_id: str) -> Optional[Deployment]:
        """Sync version for background workers. Uses sync session."""
        return (
            db.query(Deployment)
            .filter(
                Deployment.whatsapp_phone_number_id == phone_number_id,
                Deployment.is_active == True
            )
            .first()
        )
