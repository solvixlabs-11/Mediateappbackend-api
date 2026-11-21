"""Employee Territory & Customer Mapping Wizard Pydantic schemas."""

from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MappingCapabilitiesResponse(BaseModel):
    """Wizard capabilities and system constraints."""

    beats: bool = False
    beats_reason: str = "Waiting for Std Route Chart design"
    max_items: int = 20000
    supported_modes: list[str] = ["TERRITORY", "CUSTOMER"]
    conflict_policies: list[str] = ["SKIP", "REPLACE", "ADD"]


class MappingPreviewRequest(BaseModel):
    """Payload to initiate a dry-run mapping preview."""

    mode: str = Field(..., pattern="^(TERRITORY|CUSTOMER)$", description="'TERRITORY' or 'CUSTOMER'")
    target_employee_id: int = Field(..., description="Target employee ID receiving assignments")
    conflict_policy: str = Field(default="SKIP", pattern="^(SKIP|REPLACE|ADD)$")
    territory_ids: list[int] = Field(default_factory=list)
    customer_type: str | None = Field(default=None, description="DOCTOR, CHEMIST, STOCKIST, HOSPITAL")
    customer_ids: list[int] = Field(default_factory=list)
    filter_state_id: int | None = None
    filter_city_id: int | None = None


class MappingConflictItem(BaseModel):
    """Conflict information for an item already assigned elsewhere."""

    entity_type: str
    entity_id: int
    entity_name: str
    current_employee_id: int | None = None
    current_employee_name: str | None = None
    resolution: str  # SKIP, REPLACE, or ADD


class MappingPreviewResponse(BaseModel):
    """Dry-run preview result before applying changes."""

    batch_id: int
    mode: str
    target_employee_id: int
    target_employee_name: str | None = None
    total_candidate_items: int
    new_assignments_count: int
    conflicts_count: int
    conflicts_sample: list[MappingConflictItem]
    sample_preview: list[dict[str, Any]]


class MappingBatchItemResponse(BaseModel):
    """Record of individual assignment item in a batch."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    action: str
    employee_id: int
    territory_id: int | None = None
    customer_type: str | None = None
    customer_id: int | None = None
    before_state: str | None = None
    after_state: str | None = None
    created_at: dt.datetime


class MappingBatchResponse(BaseModel):
    """Summary of a mapping batch execution."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    mode: str
    status: str
    target_employee_id: int | None = None
    target_employee_name: str | None = None
    conflict_policy: str
    counts: dict[str, int] | None = None
    applied_at: dt.datetime | None = None
    reverted_at: dt.datetime | None = None
    created_at: dt.datetime


class MappingBatchDetailResponse(BaseModel):
    """Detailed view of a batch with its applied items."""

    batch: MappingBatchResponse
    items: list[MappingBatchItemResponse]
    total_items: int
    page: int
    page_size: int
