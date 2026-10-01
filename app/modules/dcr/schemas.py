"""Daily Call Report (DCR) and Planning Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# 1. Planned Visits (Feature 8)
class PlannedVisitCreate(BaseModel):
    """Payload to create a planned visit."""

    plan_date: date = Field(..., description="Target visit date")
    customer_type: str = Field(..., description="DOCTOR, CHEMIST, HOSPITAL, STOCKIST")
    doctor_id: int | None = None
    chemist_id: int | None = None
    hospital_id: int | None = None
    stockist_id: int | None = None
    priority: str = Field(default="MEDIUM", description="HIGH, MEDIUM, LOW")
    visit_purpose: str | None = None
    notes: str | None = None
    client_uuid: str | None = Field(default=None, max_length=64)


class PlannedVisitUpdate(BaseModel):
    """Payload to update a planned visit."""

    priority: str | None = None
    visit_purpose: str | None = None
    status: str | None = None  # PLANNED, COMPLETED, MISSED, CANCELLED
    notes: str | None = None


class PlannedVisitResponse(BaseModel):
    """Planned visit details response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    plan_date: date
    customer_type: str
    doctor_id: int | None = None
    chemist_id: int | None = None
    hospital_id: int | None = None
    stockist_id: int | None = None
    customer_name: str | None = None
    priority: str
    visit_purpose: str | None = None
    status: str
    notes: str | None = None
    client_uuid: str | None = None
    created_at: datetime


# 2. DCR Product Discussion & Samples (P4-B-01 & P4-B-02)
class DcrProductDetailCreate(BaseModel):
    """Products discussed and samples given."""

    product_name: str = Field(..., max_length=150)
    sample_quantity: int = Field(default=0, ge=0)
    gift_quantity: int = Field(default=0, ge=0)
    remarks: str | None = None


class DcrProductDetailResponse(BaseModel):
    """Product discussion line item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    sample_quantity: int
    gift_quantity: int
    remarks: str | None = None


# 3. Post-Call Analysis (Feature 9)
class DcrPostCallAnalysisCreate(BaseModel):
    """Customer reaction and feedback."""

    call_outcome: str = Field(
        default="HIGHLY_INTERESTED",
        description="HIGHLY_INTERESTED, MODERATE, NOT_INTERESTED, BUSY_RESCHEDULED",
    )
    doctor_feedback: str | None = None
    prescription_commitment: str = Field(default="HIGH", description="HIGH, MEDIUM, LOW, NIL")
    next_visit_date: date | None = None
    follow_up_required: bool = False
    follow_up_notes: str | None = None


class DcrPostCallAnalysisResponse(BaseModel):
    """Post-call analysis response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    call_outcome: str
    doctor_feedback: str | None = None
    prescription_commitment: str
    next_visit_date: date | None = None
    follow_up_required: bool
    follow_up_notes: str | None = None
    created_at: datetime


# 4. DCR Visit (Feature 7)
class DcrVisitCreate(BaseModel):
    """Complete DCR submission payload with GPS and post-call feedback."""

    dcr_date: date = Field(..., description="Date of the visit")
    customer_type: str = Field(..., description="DOCTOR, CHEMIST, HOSPITAL, STOCKIST")
    doctor_id: int | None = None
    chemist_id: int | None = None
    hospital_id: int | None = None
    stockist_id: int | None = None
    planned_visit_id: int | None = None

    visit_type: str = Field(
        default="INDEPENDENT",
        description="INDEPENDENT, JOINT_WITH_MANAGER, HOSPITAL_OPD",
    )
    joint_manager_id: int | None = None
    call_time: datetime | None = None
    call_duration_minutes: int = Field(default=15, ge=1, le=480)

    # GPS coordinates
    latitude: float | None = None
    longitude: float | None = None
    location_accuracy: float | None = None
    is_mock_location: bool = False

    remarks: str | None = None
    pob_amount: float = Field(default=0.0, ge=0.0)

    post_call_analysis: DcrPostCallAnalysisCreate | None = None
    product_details: list[DcrProductDetailCreate] = Field(default_factory=list)
    client_uuid: str | None = Field(default=None, max_length=64)


class DcrVisitResponse(BaseModel):
    """DCR visit response with calculated geofence status."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    dcr_date: date
    customer_type: str
    doctor_id: int | None = None
    chemist_id: int | None = None
    hospital_id: int | None = None
    stockist_id: int | None = None
    customer_name: str | None = None
    planned_visit_id: int | None = None
    visit_type: str
    joint_manager_id: int | None = None
    call_time: datetime
    call_duration_minutes: int

    # Geofence server verification
    latitude: float | None = None
    longitude: float | None = None
    location_accuracy: float | None = None
    distance_to_customer_meters: float | None = None
    is_geofence_verified: bool
    geofence_radius_meters: float
    is_mock_location: bool

    remarks: str | None = None
    pob_amount: float
    status: str
    client_uuid: str | None = None
    created_at: datetime

    post_call_analysis: DcrPostCallAnalysisResponse | None = None
    product_details: list[DcrProductDetailResponse] = []


# 5. Follow-ups (Feature 23)
class FollowUpCreate(BaseModel):
    """Payload to create customer follow-up."""

    customer_type: str = Field(..., description="DOCTOR, CHEMIST, HOSPITAL, STOCKIST")
    doctor_id: int | None = None
    chemist_id: int | None = None
    hospital_id: int | None = None
    stockist_id: int | None = None
    dcr_visit_id: int | None = None
    due_date: date
    title: str = Field(..., max_length=150)
    notes: str | None = None
    priority: str = Field(default="MEDIUM", description="HIGH, MEDIUM, LOW")
    client_uuid: str | None = Field(default=None, max_length=64)


class FollowUpResponse(BaseModel):
    """Follow-up response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    customer_type: str
    doctor_id: int | None = None
    chemist_id: int | None = None
    hospital_id: int | None = None
    stockist_id: int | None = None
    customer_name: str | None = None
    dcr_visit_id: int | None = None
    due_date: date
    title: str
    notes: str | None = None
    priority: str
    status: str
    completed_at: datetime | None = None
    client_uuid: str | None = None
    created_at: datetime


class DcrDailySummary(BaseModel):
    """Daily summary metrics for MR."""

    dcr_date: date
    total_calls: int
    doctor_calls: int
    chemist_calls: int
    hospital_calls: int
    stockist_calls: int
    geofence_verified_count: int
    total_pob_amount: float
    planned_calls_count: int
    missed_calls_count: int
