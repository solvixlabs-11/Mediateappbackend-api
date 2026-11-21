"""Schemas for Admin Visits bulk operations (Delete My Visits & Restore)."""

from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class DeleteVisitsPreviewRequest(BaseModel):
    """Filter parameters to preview visits targeted for bulk deletion."""

    employee_ids: list[int] | None = Field(default=None, description="Employee IDs to delete visits for")
    city_ids: list[int] | None = Field(default=None, description="City IDs")
    area_ids: list[int] | None = Field(default=None, description="Area IDs")
    start_date: date | None = Field(default=None, description="Start date (inclusive)")
    end_date: date | None = Field(default=None, description="End date (inclusive)")
    customer_type: str | None = Field(default=None, description="DOCTOR, CHEMIST, STOCKIST, HOSPITAL, or ALL")
    visit_type: str | None = Field(default=None, description="INDEPENDENT, JOINT_WITH_MANAGER, etc.")


class VisitSampleItem(BaseModel):
    """Summary of a visit in the deletion preview sample."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    dcr_date: date
    customer_type: str
    customer_name: str | None = None
    employee_id: int
    employee_name: str | None = None
    city: str | None = None
    pob_amount: float = 0.0


class DeleteVisitsPreviewResponse(BaseModel):
    """Response containing matching count, preview token, and sample records."""

    total_matching_visits: int
    preview_token: str
    expires_at: datetime
    max_limit_allowed: int = 5000
    sample_visits: list[VisitSampleItem]


class DeleteVisitsExecuteRequest(BaseModel):
    """Payload to execute bulk soft delete with security validation."""

    preview_token: str = Field(..., description="Active token generated from delete-preview")
    reason: str = Field(..., min_length=5, description="Audited business justification for deletion")
    confirm_text: str | None = Field(default=None, description="Optional safety phrase confirmation")


class DeleteVisitsExecuteResponse(BaseModel):
    """Execution summary of deleted visits and side effect rollbacks."""

    deleted_count: int
    planned_visits_reverted: int
    follow_ups_cancelled: int
    deletion_token: str
    message: str


class RestoreVisitsRequest(BaseModel):
    """Payload to restore previously soft-deleted visits."""

    deletion_token: str | None = Field(default=None, description="Token of the deletion batch")
    visit_ids: list[int] | None = Field(default=None, description="Explicit visit IDs to restore")
    reason: str | None = Field(default=None, description="Reason for restoration")


class RestoreVisitsResponse(BaseModel):
    """Execution summary of restored visits."""

    restored_count: int
    planned_visits_restored: int
    follow_ups_restored: int
    message: str
