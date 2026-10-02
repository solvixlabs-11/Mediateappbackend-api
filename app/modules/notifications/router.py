"""Notifications REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.notifications.schemas import (
    DeviceTokenRegisterRequest,
    DeviceTokenResponse,
    NotificationCreate,
    NotificationResponse,
    NotificationSummaryResponse,
)
from app.modules.notifications.service import NotificationService
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/summary",
    response_model=NotificationSummaryResponse,
    summary="Get unread badge counters",
)
def get_notification_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationSummaryResponse:
    """Return count of unread and total notifications."""
    service = NotificationService(db)
    return service.get_summary(current_user.id)


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="List notifications for current user",
)
def list_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    notification_type: str | None = Query(None, description="APPROVAL, TASK, LEAVE, TOUR, EXPENSE, SYSTEM"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationResponse]:
    """Get list of user notifications."""
    service = NotificationService(db)
    return service.list_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        notification_type=notification_type,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or trigger a notification",
)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    """Create a notification."""
    service = NotificationService(db)
    return service.create_notification(payload)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark single notification as read",
)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    """Mark a notification as read."""
    service = NotificationService(db)
    return service.mark_as_read(current_user.id, notification_id)


@router.post(
    "/read-all",
    summary="Mark all notifications as read",
)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Mark all unread notifications read."""
    service = NotificationService(db)
    return service.mark_all_as_read(current_user.id)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notification",
)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete single notification."""
    service = NotificationService(db)
    service.delete_notification(current_user.id, notification_id)


@router.post(
    "/device-token",
    response_model=DeviceTokenResponse,
    summary="Register push notification device token",
)
def register_device_token(
    payload: DeviceTokenRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceTokenResponse:
    """Register device token for push notifications."""
    service = NotificationService(db)
    return service.register_device_token(current_user.id, payload)
