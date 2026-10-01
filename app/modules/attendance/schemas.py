"""Attendance Pydantic schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class AttendanceCheckInRequest(BaseModel):
    """Payload to record daily morning check-in."""

    date: dt.date | None = None
    latitude: float = Field(..., description="Current device latitude")
    longitude: float = Field(..., description="Current device longitude")
    accuracy: float | None = Field(default=None, description="GPS accuracy in meters")
    address: str | None = Field(default=None, max_length=255)
    mock_location_flag: bool = False
    remarks: str | None = None
    client_uuid: str | None = Field(default=None, max_length=64)


class AttendanceCheckOutRequest(BaseModel):
    """Payload to record end-of-day check-out."""

    latitude: float = Field(..., description="Current device latitude")
    longitude: float = Field(..., description="Current device longitude")
    accuracy: float | None = Field(default=None, description="GPS accuracy in meters")
    address: str | None = Field(default=None, max_length=255)
    mock_location_flag: bool = False
    remarks: str | None = None


class AttendanceResponse(BaseModel):
    """Daily attendance details response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date: dt.date
    status: str
    check_in_time: dt.datetime | None = None
    check_in_latitude: float | None = None
    check_in_longitude: float | None = None
    check_in_address: str | None = None
    check_in_accuracy: float | None = None
    check_in_mock_flag: bool = False
    check_out_time: dt.datetime | None = None
    check_out_latitude: float | None = None
    check_out_longitude: float | None = None
    check_out_address: str | None = None
    check_out_accuracy: float | None = None
    check_out_mock_flag: bool = False
    total_work_minutes: int | None = None
    remarks: str | None = None
    client_uuid: str | None = None
    created_at: dt.datetime
