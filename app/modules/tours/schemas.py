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
