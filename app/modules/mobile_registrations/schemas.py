"""Mobile registration schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MobileRegistrationResponse(BaseModel):
    """Mobile registration single item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    registration_code: str
    employee_id: int
    employee_name: str | None = None
    employee_email: str | None = None
    designation: str | None = None
    territory: str | None = None
    city: str | None = None
    state: str | None = None
    device_id_hash: str | None = None
    device_model: str | None = None
    app_version: str | None = None
    status: str
    requested_at: datetime
    decided_by_id: int | None = None
    decided_by_name: str | None = None
    decided_at: datetime | None = None
    comment: str | None = None
    created_at: datetime
    updated_at: datetime


class MobileRegistrationListResponse(BaseModel):
    """Paginated mobile registration response."""

    items: list[MobileRegistrationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    pending_count: int


class MobileRegistrationBulkActionRequest(BaseModel):
    """Payload to bulk approve or reject registrations."""

    ids: list[int] = Field(..., min_length=1, description="List of registration IDs")
    comment: str | None = Field(default=None, description="Approval or rejection notes")


class MobileRegistrationRowResult(BaseModel):
    """Per-row outcome for bulk action."""

    id: int
    success: bool
    status: str
    message: str | None = None


class MobileRegistrationBulkActionResponse(BaseModel):
    """Summary of bulk action outcomes."""

    total_processed: int
    success_count: int
    failure_count: int
    results: list[MobileRegistrationRowResult]
