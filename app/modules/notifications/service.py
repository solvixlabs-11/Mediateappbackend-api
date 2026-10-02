"""Service layer for in-app notifications and push notifications."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import (
    DeviceTokenRegisterRequest,
    DeviceTokenResponse,
    NotificationCreate,
    NotificationResponse,
    NotificationSummaryResponse,
)


class NotificationService:
    """Business operations on notifications."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = NotificationRepository(db)

    def _to_response(self, notif: Notification) -> NotificationResponse:
        return NotificationResponse(
            id=notif.id,
            user_id=notif.user_id,
            title=notif.title,
            body=notif.body,
            notification_type=notif.notification_type,
            reference_id=notif.reference_id,
            is_read=notif.is_read,
            read_at=notif.read_at,
            created_at=notif.created_at,
        )

    def list_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        notification_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NotificationResponse]:
        """Fetch notifications for current user."""
        items = self.repo.list_by_user(
            user_id=user_id,
            unread_only=unread_only,
            notification_type=notification_type,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(n) for n in items]

    def get_summary(self, user_id: int) -> NotificationSummaryResponse:
        """Count unread and total for badges."""
        data = self.repo.count_summary(user_id)
        return NotificationSummaryResponse(**data)

    def mark_as_read(self, user_id: int, notification_id: int) -> NotificationResponse:
        """Mark single notification as read."""
        notif = self.repo.get_by_id(notification_id, user_id)
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found.",
            )
        self.repo.mark_as_read(notif)
        self.db.commit()
        return self._to_response(notif)

    def mark_all_as_read(self, user_id: int) -> dict[str, int]:
        """Mark all unread notifications as read."""
        affected = self.repo.mark_all_as_read(user_id)
        self.db.commit()
        return {"marked_read_count": affected}

    def delete_notification(self, user_id: int, notification_id: int) -> None:
        """Delete notification."""
        notif = self.repo.get_by_id(notification_id, user_id)
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found.",
            )
        self.repo.delete(notif)
        self.db.commit()

    def create_notification(self, payload: NotificationCreate) -> NotificationResponse:
        """Create a new notification."""
        notif = self.repo.create(
            user_id=payload.user_id,
            title=payload.title,
            body=payload.body,
            notification_type=payload.notification_type,
            reference_id=payload.reference_id,
        )
        self.db.commit()
        return self._to_response(notif)

    def register_device_token(
        self, user_id: int, payload: DeviceTokenRegisterRequest
    ) -> DeviceTokenResponse:
        """Register push device token."""
        token = self.repo.upsert_device_token(
            user_id=user_id,
            token=payload.token,
            platform=payload.platform,
        )
        self.db.commit()
        return DeviceTokenResponse(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            platform=token.platform,
            is_active=token.is_active,
            created_at=token.created_at,
        )
