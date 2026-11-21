"""System Configuration & Geofence Settings Pydantic schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class SettingResponse(BaseModel):
    """Single application setting response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    group: str
    value: str
    value_type: str
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    allowed_options: list[str] | None = None
    help_text: str | None = None
    is_provisional: bool = False
    updated_at: dt.datetime


class SettingUpdateRequest(BaseModel):
    """Payload to update a single setting."""

    value: str = Field(..., description="New setting value as string")
    reason: str | None = Field(default=None, max_length=255, description="Audit reason for change")


class SettingBulkItem(BaseModel):
    """Single item in bulk settings update."""

    key: str
    value: str


class SettingBulkUpdateRequest(BaseModel):
    """Payload to update multiple settings in a transaction."""

    settings: list[SettingBulkItem]
    reason: str | None = Field(default=None, max_length=255)


class SettingGroupResponse(BaseModel):
    """Group of settings with group metadata."""

    group: str
    title: str
    description: str | None = None
    settings: list[SettingResponse]


class SettingHistoryResponse(BaseModel):
    """Historical change record for a setting."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    old_value: str | None = None
    new_value: str
    changed_by: int | None = None
    change_summary: str | None = None
    created_at: dt.datetime


class GeofenceSettingResponse(BaseModel):
    """Geofence rule for a customer type."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    radius_m: float
    min_accuracy_m: float
    is_provisional: bool = False
    is_active: bool = True
    updated_at: dt.datetime


class GeofenceSettingUpdateItem(BaseModel):
    """Single geofence rule update item."""

    entity_type: str
    radius_m: float = Field(..., ge=10, le=5000, description="Radius in meters (10 to 5000)")
    min_accuracy_m: float = Field(default=50.0, ge=5, le=500, description="Min GPS accuracy in meters")
    is_provisional: bool | None = None


class GeofenceBulkUpdateRequest(BaseModel):
    """Payload to update all geofence settings."""

    items: list[GeofenceSettingUpdateItem]
    reason: str | None = Field(default=None, max_length=255)
