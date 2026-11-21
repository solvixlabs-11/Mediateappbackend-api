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


class ExpenseLimitResponse(BaseModel):
    """Designation expense limit response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    designation_id: int | None = None
    designation_code: str
    expense_type_id: int | None = None
    expense_type_code: str
    daily_limit: float
    monthly_limit: float
    effective_from: dt.date
    is_provisional: bool = False
    updated_at: dt.datetime


class ExpenseLimitBulkItem(BaseModel):
    """Single item in bulk expense limits upsert."""

    designation_code: str
    expense_type_code: str
    daily_limit: float = Field(..., ge=0, description="Daily limit in INR")
    monthly_limit: float = Field(..., ge=0, description="Monthly limit in INR")
    effective_from: dt.date | None = None
    is_provisional: bool | None = None


class ExpenseLimitBulkUpsertRequest(BaseModel):
    """Payload to upsert matrix of expense limits."""

    items: list[ExpenseLimitBulkItem]
    reason: str | None = Field(default=None, max_length=255)


class ExpenseLimitMatrixCell(BaseModel):
    """Limit details for a single designation x expense type cell."""

    id: int | None = None
    daily_limit: float
    monthly_limit: float
    is_provisional: bool = False


class ExpenseLimitMatrixRow(BaseModel):
    """Matrix row for a designation."""

    designation_code: str
    designation_name: str
    limits: dict[str, ExpenseLimitMatrixCell]  # expense_type_code -> cell


class ExpenseLimitMatrixResponse(BaseModel):
    """Matrix response of all designations x expense types."""

    designations: list[dict[str, str]]  # list of {code, name}
    expense_types: list[dict[str, str]]  # list of {code, name}
    rows: list[ExpenseLimitMatrixRow]


class ExpensePayoutRequest(BaseModel):
    """Payload to settle/pay out an approved expense claim."""

    payment_date: dt.date = Field(default_factory=dt.date.today)
    reference_no: str = Field(..., max_length=100, description="UTR / Bank transaction reference")
    payment_mode: str = Field(default="NEFT", max_length=50, description="NEFT, RTGS, UPI, CHEQUE, CASH")
    remarks: str | None = Field(default=None, max_length=255)
    idempotency_key: str | None = Field(default=None, max_length=64, description="Client UUID for duplicate protection")


class ExpensePayoutResponse(BaseModel):
    """Processed payout record."""

    id: int
    expense_id: int
    amount: float
    payment_mode: str
    reference_no: str
    payment_date: dt.date
    processed_by_id: int
    idempotency_key: str | None = None
    remarks: str | None = None
    created_at: dt.datetime



