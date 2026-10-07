"""Pydantic schemas for Targets."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TargetCreateOrUpdate(BaseModel):
    """Payload to create or update an MR's monthly target."""

    user_id: int = Field(..., description="Target MR user ID")
    year: int = Field(..., ge=2020, le=2050, description="Target year")
    month: int = Field(..., ge=1, le=12, description="Target month (1-12)")
    visit_target: int = Field(0, ge=0, description="Monthly call/visit target")
    doctor_call_target: int = Field(0, ge=0, description="Doctor visit target")
    chemist_call_target: int = Field(0, ge=0, description="Chemist visit target")
    primary_sales_target: float = Field(0.0, ge=0.0, description="Primary sales target (Rs)")
    secondary_sales_target: float = Field(
        0.0, ge=0.0, description="Secondary sales / POB target (Rs)"
    )


class TargetResponse(BaseModel):
    """Response representation of a target."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str | None = None
    year: int
    month: int
    visit_target: int
    doctor_call_target: int
    chemist_call_target: int
    primary_sales_target: float
    secondary_sales_target: float


class TargetsListResponse(BaseModel):
    """List of targets returned for a month/year query."""

    year: int
    month: int
    items: list[TargetResponse]
