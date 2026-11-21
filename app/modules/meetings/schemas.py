"""Pydantic schemas for Meetings Workflow."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MeetingResponse(BaseModel):
    """Single meeting response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    agenda: str
    meeting_type: str
    start_date: datetime
    end_date: datetime
    created_by_id: int
    created_by_name: str | None = None
    organiser_id: int
    organiser_name: str | None = None
    location: str | None = None
    status: str
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class MeetingCreateRequest(BaseModel):
    """Payload to create a meeting (Draft or Applied)."""

    agenda: str = Field(..., max_length=255)
    meeting_type: str = Field(default="CYCLE_MEETING", max_length=50)
    start_date: datetime
    end_date: datetime
    organiser_id: int | None = None
    location: str | None = Field(default=None, max_length=255)
    remarks: str | None = None
    status: str = Field(default="DRAFT", description="DRAFT or APPLIED")


class MeetingUpdateRequest(BaseModel):
    """Payload to update an existing meeting."""

    agenda: str | None = Field(default=None, max_length=255)
    meeting_type: str | None = Field(default=None, max_length=50)
    start_date: datetime | None = None
    end_date: datetime | None = None
    organiser_id: int | None = None
    location: str | None = Field(default=None, max_length=255)
    remarks: str | None = None
    status: str | None = None


class MeetingSummaryResponse(BaseModel):
    """3-Tile workflow summary counts for meetings."""

    drafts: int
    applied: int
    received: int
    total: int
