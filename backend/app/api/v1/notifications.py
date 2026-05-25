import uuid
from typing import List
from fastapi import APIRouter, Depends, status, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationCreate
from app.services.notification import NotificationService
from app.services.websocket import manager

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: str = Query(...), 
):
    """WebSocket endpoint for real-time notifications."""
    user_id_str = decode_access_token(token)
    if not user_id_str:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    await manager.connect(websocket, user_id)
    try:
        while True:
            # We don't expect messages from the client right now.
            # Just keep connection open and listen for disconnects.
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)

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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new notification for the current authenticated user."""
    notif = NotificationService.create_notification(db, current_user.id, payload.title, payload.details)
    
    # Push to connected websocket client
    message = {
        "id": str(notif.id),
        "title": notif.title,
        "details": notif.details,
        "read": notif.read,
        "created_at": notif.created_at.isoformat()
    }
    background_tasks.add_task(manager.send_personal_message, message, current_user.id)
    
    return notif

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
