"""Repository for notifications and push device tokens."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.notifications.models import DeviceToken, Notification


class NotificationRepository:
    """Handles database transactions for notifications."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user(
        self,
        user_id: int,
        unread_only: bool = False,
        notification_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Notification]:
        """Fetch notifications for a specific user ordered latest first."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)  # noqa: E712
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type.upper())

        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def count_summary(self, user_id: int) -> dict[str, int]:
        """Count unread and total notifications."""
        total = self.db.query(Notification).filter(Notification.user_id == user_id).count()
        unread = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .count()
        )
        return {"unread_count": unread, "total_count": total}

    def get_by_id(self, notification_id: int, user_id: int) -> Notification | None:
        """Fetch notification belonging to user."""
        return (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

    def create(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: str = "SYSTEM",
        reference_id: str | None = None,
    ) -> Notification:
        """Create notification."""
        notif = Notification(
            user_id=user_id,
            title=title.strip(),
            body=body.strip(),
            notification_type=notification_type.upper(),
            reference_id=reference_id,
            is_read=False,
            created_at=datetime.utcnow(),
        )
        self.db.add(notif)
        self.db.flush()
        return notif

    def mark_as_read(self, notification: Notification) -> Notification:
        """Mark single notification read."""
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.db.flush()
        return notification

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all unread notifications as read for a user."""
        now = datetime.utcnow()
        affected = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .update({"is_read": True, "read_at": now}, synchronize_session="fetch")
        )
        self.db.flush()
        return affected

    def delete(self, notification: Notification) -> None:
        """Delete notification."""
        self.db.delete(notification)
        self.db.flush()

    def upsert_device_token(
        self, user_id: int, token: str, platform: str = "ANDROID"
    ) -> DeviceToken:
        """Register or update device push token."""
        record = self.db.query(DeviceToken).filter(DeviceToken.token == token).first()
        now = datetime.utcnow()
        if record:
            record.user_id = user_id
            record.platform = platform.upper()
            record.is_active = True
            record.updated_at = now
        else:
            record = DeviceToken(
                user_id=user_id,
                token=token,
                platform=platform.upper(),
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            self.db.add(record)
        self.db.flush()
        return record
