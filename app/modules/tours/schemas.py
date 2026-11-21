"""Tour Program Pydantic schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class TourProgramCreateRequest(BaseModel):
    """Payload to submit a new tour program."""

    title: str = Field(..., max_length=150, description="Tour program title")
    start_date: dt.date = Field(..., description="Tour start date")
    end_date: dt.date = Field(..., description="Tour end date")
    route_details: str | None = Field(
        default=None, max_length=255, description="Target cities or territories"
    )
    objectives: str | None = Field(default=None, description="Key tour targets and customer visits")
    admin_override_reason: str | None = Field(
        default=None, description="Admin justification to override an active cutoff lock"
    )


class TourProgramResponse(BaseModel):
    """Tour Program details response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str | None = None
    title: str
    start_date: dt.date
    end_date: dt.date
    total_days: int
    route_details: str | None = None
    objectives: str | None = None
    status: str
    approval_request_id: int | None = None
    rejection_reason: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime


class TourPlanLockCreateRequest(BaseModel):
    """Payload to establish a cutoff lock on tour plans."""

    scope: str = Field(default="ALL", description="Lock scope: ALL, TERRITORY, or EMPLOYEE")
    scope_id: int | None = Field(default=None, description="Target territory ID or employee ID")
    month: int = Field(..., ge=1, le=12, description="Target month (1-12)")
    year: int = Field(..., ge=2020, le=2050, description="Target calendar year")
    financial_year: str = Field(default="2026-2027", max_length=20, description="e.g. 2026-2027")
    cutoff_date: dt.date = Field(..., description="Cutoff submission deadline date")
    reason: str | None = Field(default=None, description="Reason for establishing lock")


class TourPlanUnlockRequest(BaseModel):
    """Payload to unlock tour plan submissions."""

    reason: str = Field(..., min_length=3, description="Audited business justification for unlocking")


class TourPlanLockResponse(BaseModel):
    """Tour plan cutoff lock response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    scope: str
    scope_id: int | None = None
    scope_name: str | None = None
    month: int
    year: int
    financial_year: str
    cutoff_date: dt.date
    status: str
    reason: str | None = None
    created_by_id: int
    created_by_name: str | None = None
    unlocked_by_id: int | None = None
    unlocked_by_name: str | None = None
    unlocked_at: dt.datetime | None = None
    created_at: dt.datetime
    updated_at: dt.datetime

