"""Dashboard Pydantic schemas for Admin Live Field Activity and MR/Manager metrics."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LiveActivitySummary(BaseModel):
    """Summary strip metrics for Admin Home."""

    model_config = ConfigDict(from_attributes=True)

    checked_in_count: int
    total_mrs: int
    total_calls_today: int
    doctors_visited: int
    chemists_visited: int
    total_pob_today: float
    attendance_pct: float
    not_checked_in_count: int


class MrLiveActivityItem(BaseModel):
    """Individual MR live field activity card item (Section 8.2)."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    mr_name: str
    employee_code: str
    profile_photo: str | None = None
    territory_name: str | None = None
    status: str  # VISITING, CHECKED_IN, IDLE, NOT_CHECKED_IN, ON_LEAVE
    check_in_time: datetime | None = None
    calls_count: int = 0
    doctors_count: int = 0
    chemists_count: int = 0
    samples_count: int = 0
    calls_target: int = 12
    last_activity_text: str | None = None
    last_activity_time: datetime | None = None
    last_activity_minutes_ago: int | None = None
    is_verified: bool = True
    latitude: float | None = None
    longitude: float | None = None


class PendingApprovalsSummary(BaseModel):
    """Summary of pending approval requests categorized by entity type."""

    model_config = ConfigDict(from_attributes=True)

    tours_count: int = 0
    expenses_count: int = 0
    leaves_count: int = 0
    total_pending: int = 0


class AdminLiveActivityResponse(BaseModel):
    """Full Admin Home Live Field Activity response (Section 8.2)."""

    model_config = ConfigDict(from_attributes=True)

    summary: LiveActivitySummary
    mr_activities: list[MrLiveActivityItem]
    pending_approvals: PendingApprovalsSummary


class MrDashboardResponse(BaseModel):
    """MR daily KPI & performance metrics."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    today_date: date
    attendance_status: str  # CHECKED_IN, CHECKED_OUT, NOT_CHECKED_IN
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    visits_today: int = 0
    visits_target: int = 12
    doctors_visited: int = 0
    chemists_visited: int = 0
    pob_today: float = 0.0
    monthly_visits: int = 0
    monthly_target: int = 240
    monthly_pob: float = 0.0
    pending_followups_count: int = 0


class ManagerDashboardResponse(BaseModel):
    """Manager team oversight & KPI metrics."""

    model_config = ConfigDict(from_attributes=True)

    team_size: int = 0
    checked_in_today: int = 0
    calls_today: int = 0
    total_pob_today: float = 0.0
    pending_approvals_count: int = 0
    team_coverage_pct: float = 0.0


class EmployeeVisitSummaryItem(BaseModel):
    """Dynamic visits summary card metrics per employee (Admin Inventory Section 3.2)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    employee_code: str
    employee_name: str
    photo_url: str | None = None
    hq_name: str
    hq_code: str
    division_name: str | None = None

    # 16 Metrics
    chemist_visits: int | None = None
    new_chemist_visits: int | None = None
    doctor_visits: int | None = None
    new_doctor_visits: int | None = None
    stockist_visits: int | None = None
    new_stockist_visits: int | None = None
    doctor_call_average: float | None = None
    missing_doctor: int | None = None
    punch_in_time: str | None = None
    first_call_time: str | None = None
    last_call_time: str | None = None
    punch_out_time: str | None = None
    morning_calls: int | None = None
    evening_calls: int | None = None
    work_duration_minutes: int | None = None
    total_pob: float | None = None

    # Dynamic metrics list for schema-driven card rendering (no hardcoding on web)
    metrics: list[MetricCardRowItem] = Field(default_factory=list)


class MetricCardRowItem(BaseModel):
    """Dynamic metric row definition inside employee card."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    value: Any = None
    formatted_value: str = "-"
    kind: str = "TABLE"  # TABLE, RECORD, TIMELINE
    color_group: str = "primary"  # primary (blue), success (green), danger (red)
    status: str = "AVAILABLE"  # AVAILABLE, COMING_SOON, EMPTY
    unavailable_reason: str | None = None


class MetricColumnItem(BaseModel):
    """Table column metadata for dynamic metric tables."""

    key: str
    label: str
    type: str = "string"  # string, number, date, time, currency, percent, status
    align: str | None = "left"


class MetricRecordField(BaseModel):
    """Key-value field definition for RECORD view."""

    key: str
    label: str
    value: Any = None
    formatted_value: str = "-"


class MetricRecordData(BaseModel):
    """Structured detail for a single RECORD drill-down view."""

    title: str | None = None
    fields: list[MetricRecordField] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    accuracy: float | None = None
    address: str | None = None
    map_pin: bool = False
    mock_flag: bool = False


class MetricTimelineEvent(BaseModel):
    """Timeline event definition for TIMELINE view."""

    time: str
    title: str
    subtitle: str | None = None
    type: str  # CHECK_IN, CHECK_OUT, CALL, GAP
    status: str | None = None
    duration_minutes: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    verified: bool = False


class MetricMeta(BaseModel):
    """Metadata describing the metric drilldown."""

    title: str
    kind: str  # TABLE, RECORD, TIMELINE
    status: str = "AVAILABLE"  # AVAILABLE, COMING_SOON
    unavailable_reason: str | None = None
    columns: list[MetricColumnItem] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    can_export: bool = True
    employee: dict[str, Any] = Field(default_factory=dict)
    generated_at: str
    data_as_of: str


class MetricDetailResponse(BaseModel):
    """Universal drilldown detail response."""

    meta: MetricMeta
    rows: list[dict[str, Any]] = Field(default_factory=list)
    record: MetricRecordData | None = None
    events: list[MetricTimelineEvent] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class VisitsSummaryResponse(BaseModel):
    """Paginated Visits Summary response."""

    model_config = ConfigDict(from_attributes=True)

    items: list[EmployeeVisitSummaryItem]
    total: int
    page: int
    page_size: int

