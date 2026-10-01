"""Approval engine Pydantic schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class ApprovalDecisionRequest(BaseModel):
    """Payload submitted by manager or admin to approve or reject a request."""

    decision: str = Field(..., description="'APPROVED' or 'REJECTED'")
    comments: str | None = Field(default=None, description="Mandatory when rejected")


class ApprovalHistoryResponse(BaseModel):
    """Single review action record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    approver_id: int
    approver_name: str | None = None
    decision: str
    comments: str | None = None
    decided_at: dt.datetime


class ApprovalRequestResponse(BaseModel):
    """Full approval request detail including requester information and review history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str  # TOUR, EXPENSE, LEAVE
    entity_id: int
    requester_id: int
    requester_name: str | None = None
    requester_email: str | None = None
    status: str  # PENDING, APPROVED, REJECTED, CANCELLED
    current_step: int
    total_steps: int
    title: str
    details: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
    history: list[ApprovalHistoryResponse] = []
