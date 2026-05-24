import uuid
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.notification import Notification

class NotificationService:
    @staticmethod
    def create_notification(db: Session, user_id: uuid.UUID, title: str, details: str) -> Notification:
        """Create a notification in the database for a specific user."""
        db_notification = Notification(
            user_id=user_id,
            title=title,
            details=details,
            read=False
        )
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        return db_notification

    @staticmethod
    def list_notifications(db: Session, user_id: uuid.UUID) -> List[Notification]:
        """List all notifications for a specific user, ordered by created_at DESC."""
        return db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def mark_as_read(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
        """Mark a specific notification as read."""
        db_notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if not db_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        db_notification.read = True
        db.commit()
        db.refresh(db_notification)
        return db_notification

    @staticmethod
    def mark_all_read(db: Session, user_id: uuid.UUID) -> List[Notification]:
        """Mark all unread notifications for a user as read."""
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).all()

        for notif in unread_notifications:
            notif.read = True

        db.commit()
        return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def delete_notification(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
        """Delete/dismiss a specific notification."""
        db_notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if not db_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        db.delete(db_notification)
        db.commit()
        return True

    @staticmethod
    def clear_all(db: Session, user_id: uuid.UUID) -> bool:
        """Delete all notifications for a user."""
        db.query(Notification).filter(
            Notification.user_id == user_id
        ).delete(synchronize_session=False)
        db.commit()
        return True
