import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationCreate
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all notifications for the current authenticated user."""
    return NotificationService.list_notifications(db, current_user.id)

@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new notification for the current authenticated user."""
    return NotificationService.create_notification(db, current_user.id, payload.title, payload.details)

@router.put("/read-all", response_model=List[NotificationResponse])
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all unread notifications for the current user as read."""
    return NotificationService.mark_all_read(db, current_user.id)

@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific notification as read."""
    return NotificationService.mark_as_read(db, current_user.id, notification_id)

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dismiss/delete a specific notification."""
    NotificationService.delete_notification(db, current_user.id, notification_id)
    return None

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all notifications for the current user."""
    NotificationService.clear_all(db, current_user.id)
    return None
