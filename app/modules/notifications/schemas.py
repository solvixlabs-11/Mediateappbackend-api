"""Pydantic schemas for notifications and device push tokens."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    """Payload to trigger a notification."""

    user_id: int
    title: str = Field(..., min_length=2, max_length=150)
    body: str = Field(..., min_length=2)
    notification_type: str = Field(default="SYSTEM")
    reference_id: str | None = None


class NotificationResponse(BaseModel):
    """Notification entity representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    body: str
    notification_type: str
    reference_id: str | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationSummaryResponse(BaseModel):
    """Unread badge counter."""

    model_config = ConfigDict(from_attributes=True)

    unread_count: int = 0
    total_count: int = 0


class DeviceTokenRegisterRequest(BaseModel):
    """Payload to register an FCM/APNS/Expo push notification token."""

    token: str = Field(..., min_length=10, max_length=255)
    platform: str = Field(default="ANDROID", description="ANDROID, IOS, WEB")


class DeviceTokenResponse(BaseModel):
    """Device token representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    token: str
    platform: str
    is_active: bool
    created_at: datetime
