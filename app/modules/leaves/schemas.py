"""Leave Management Pydantic schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class LeaveBalanceResponse(BaseModel):
    """Leave balances overview for user."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    casual_leave_balance: float
    sick_leave_balance: float
    earned_leave_balance: float
    total_balance: float


class LeaveApplyRequest(BaseModel):
    """Payload to apply for employee leave."""

    leave_type: str = Field(..., description="'CASUAL', 'SICK', or 'EARNED'")
    start_date: dt.date = Field(..., description="Leave start date")
    end_date: dt.date = Field(..., description="Leave end date")
    days_count: float = Field(
        default=1.0, gt=0, description="Total days (supports half-day e.g. 0.5)"
    )
    reason: str = Field(..., min_length=3, max_length=255, description="Reason for leave")
    client_uuid: str | None = Field(default=None, max_length=64)


class LeaveResponse(BaseModel):
    """Leave request response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str | None = None
    leave_type: str
    start_date: dt.date
    end_date: dt.date
    days_count: float
    reason: str
    status: str
    approval_request_id: int | None = None
    rejection_reason: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
