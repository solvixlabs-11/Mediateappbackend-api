"""Pydantic schemas for Workflow Inbox."""

from __future__ import annotations

import datetime as dt
from pydantic import BaseModel, ConfigDict


class WorkflowSummaryResponse(BaseModel):
    """Dynamic counts for the three workflow tiles (Drafts, Applied, Received)."""

    module: str
    drafts: int
    applied: int
    received: int


class WorkflowItemResponse(BaseModel):
    """Single item in the workflow inbox table."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    module: str
    entity_type: str
    entity_id: int
    approval_request_id: int | None = None
    title: str
    requester_id: int
    requester_name: str
    requester_email: str | None = None
    details: str | None = None
    status: str
    created_at: dt.datetime
    updated_at: dt.datetime
    actions: list[str] = []
