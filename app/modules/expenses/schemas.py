"""Expense Claims Pydantic schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCreateRequest(BaseModel):
    """Payload to log a daily field expense claim."""

    expense_date: dt.date = Field(..., description="Date expense occurred")
    expense_type: str = Field(
        ...,
        description="'DAILY_ALLOWANCE', 'TRAVEL_FARE', 'LODGING', or 'MISCELLANEOUS'",
    )
    amount: float = Field(..., gt=0, description="Amount claimed in INR")
    description: str | None = Field(default=None, max_length=255)
    receipt_file_id: int | None = Field(
        default=None, description="Optional uploaded receipt file ID"
    )
    client_uuid: str | None = Field(default=None, max_length=64)


class ExpenseResponse(BaseModel):
    """Expense record response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str | None = None
    expense_date: dt.date
    expense_type: str
    amount: float
    description: str | None = None
    receipt_file_id: int | None = None
    status: str
    approval_request_id: int | None = None
    rejection_reason: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime


class MonthlyExpenseSummaryResponse(BaseModel):
    """Summary of monthly expenses for reporting and claim tracking."""

    year: int
    month: int
    total_claimed: float
    total_approved: float
    total_rejected: float
    total_pending: float
    claim_count: int
