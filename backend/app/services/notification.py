import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.notification import Notification


class NotificationService:
    @staticmethod
    async def create_notification(db: AsyncSession, user_id: uuid.UUID, title: str, details: str) -> Notification:
        db_notification = Notification(
            user_id=user_id,
            title=title,
            details=details,
            read=False
        )
        db.add(db_notification)
        await db.commit()
        await db.refresh(db_notification)
        return db_notification

    @staticmethod
    async def list_notifications(db: AsyncSession, user_id: uuid.UUID) -> List[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def mark_as_read(db: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        db_notification = result.scalar_one_or_none()

        if not db_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        db_notification.read = True
        await db.commit()
        await db.refresh(db_notification)
        return db_notification

    @staticmethod
    async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> List[Notification]:
        result = await db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.read == False
            )
        )
        unread_notifications = list(result.scalars().all())

        for notif in unread_notifications:
            notif.read = True

        await db.commit()

        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_notification(db: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        db_notification = result.scalar_one_or_none()

        if not db_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        await db.delete(db_notification)
        await db.commit()
        return True

    @staticmethod
    async def clear_all(db: AsyncSession, user_id: uuid.UUID) -> bool:
        from sqlalchemy import delete as delete_stmt
        await db.execute(
            delete_stmt(Notification).where(Notification.user_id == user_id)
        )
        await db.commit()
        return True
