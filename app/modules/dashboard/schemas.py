"""Dashboard Pydantic schemas for Admin Live Field Activity and MR/Manager metrics."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


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
