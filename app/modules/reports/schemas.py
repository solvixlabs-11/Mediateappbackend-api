"""Pydantic schemas for Reports & Analytics Engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReportColumn(BaseModel):
    """Column definition for report tabular views and exports."""

    key: str
    label: str
    type: str = "string"  # string, number, date, currency, percent, status
    align: str = "left"  # left, center, right


class ReportFilterSchema(BaseModel):
    """Declarative filter options supported by a specific report."""

    date_range: bool = True
    mr_picker: bool = True
    manager_picker: bool = False
    territory_picker: bool = False
    customer_type_picker: bool = False
    status_picker: bool = False
    status_options: list[str] = Field(default_factory=list)
    specialization_picker: bool = False
    category_picker: bool = False
    category_options: list[str] = Field(default_factory=lambda: ["All", "A", "B", "C"])
    active_picker: bool = False
    work_type_picker: bool = False
    visit_type_picker: bool = False
    verified_picker: bool = False
    deviation_type_picker: bool = False
    days_not_seen_picker: bool = False


class ReportCatalogItem(BaseModel):
    """Metadata item in the reports catalog."""

    key: str
    title: str
    group: str  # Master Lists, Attendance and Daily Work, Visits, Doctor Analysis, Stock and Orders, Sales and Finance, Other
    description: str
    filter_schema: ReportFilterSchema
    available_formats: list[str] = Field(default_factory=lambda: ["json", "xlsx", "pdf"])
    status: str = "NOW"  # "NOW", "P8", "SALES", "ASK"
    is_ready: bool = True
    coming_soon_reason: str | None = None
    report_number: int | None = None


class ReportCatalogResponse(BaseModel):
    """List of accessible reports for caller's role."""

    role: str = ""
    groups: list[str] = Field(default_factory=list)
    reports: list[ReportCatalogItem]
    scope_label: str


class ReportFilterParams(BaseModel):
    """Runtime filter arguments supplied to report queries."""

    from_date: str | None = None
    to_date: str | None = None
    mr_id: int | None = None
    manager_id: int | None = None
    territory_id: int | None = None
    customer_type: str | None = None
    status: str | None = None
    specialization: str | None = None
    category: str | None = None
    active: bool | None = None
    work_type: str | None = None
    visit_type: str | None = None
    verified: bool | None = None
    deviation_type: str | None = None
    days_not_seen: int | None = None
    page: int = 1
    page_size: int = 50


class ReportMeta(BaseModel):
    """Header metadata for a report generation result."""

    key: str
    report_key: str = ""
    title: str
    group: str
    filters: dict[str, Any]
    scope_label: str
    user_scope: str = ""
    generated_at: str
    columns: list[ReportColumn] = Field(default_factory=list)
    total_records: int = 0
    landscape: bool = False


class ReportResponse(BaseModel):
    """Standard JSON response for a paged report."""

    meta: ReportMeta
    columns: list[ReportColumn] = Field(default_factory=list)
    summary: dict[str, Any]
    items: list[dict[str, Any]]
    total: int
    total_records: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


# Backward compatibility schemas for mobile dashboard
class ReportsSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_calls: int = 0
    doctor_calls: int = 0
    chemist_calls: int = 0
    hospital_calls: int = 0
    stockist_calls: int = 0
    total_pob: float = 0.0
    average_calls_per_day: float = 0.0
    total_attendance_days: int = 0
    geofence_compliance_rate: float = 0.0
    pending_approvals_count: int = 0
    active_mrs_count: int = 0


class MRPerformanceReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    user_name: str
    email: str
    territory_name: str | None = None
    total_calls: int = 0
    total_pob: float = 0.0
    call_average: float = 0.0
    geofence_verified_calls: int = 0
    geofence_compliance: float = 0.0
    attendance_days: int = 0


class CustomerCoverageReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_type: str
    total_customers: int = 0
    visited_customers: int = 0
    coverage_percentage: float = 0.0
    pending_follow_ups: int = 0


class ReportsDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: ReportsSummaryResponse
    mr_performances: list[MRPerformanceReportItem]
    customer_coverage: list[CustomerCoverageReportItem]


# -------------------------------------------------------------
# Catalog v3 Schemas
# -------------------------------------------------------------

class ReportDefinitionItem(BaseModel):
    """Schema for individual report catalog entry in v3."""

    key: str
    name: str
    group: str
    description: str | None = None
    sort_order: int = 0
    status: str = "AVAILABLE"  # AVAILABLE or COMING_SOON
    unavailable_reason: str | None = None
    formats: list[str] = Field(default_factory=list)
    filter_schema: dict[str, Any] = Field(default_factory=dict)
    allowed_roles: list[str] = Field(default_factory=list)
    data_as_of_source: str | None = None
    is_active: bool = True


class ReportCatalogV3Response(BaseModel):
    """Schema for reports catalog list response."""

    items: list[ReportDefinitionItem]
    total: int
    page: int = 1
    page_size: int = 20
    groups: list[str] = Field(default_factory=list)


class ReportOptionItem(BaseModel):
    """Single item for schema-driven dynamic filter dropdown options."""

    value: Any
    label: str
    parent_id: Any | None = None


class ReportOptionsResponse(BaseModel):
    """Response containing filter dropdown options."""

    source: str
    options: list[ReportOptionItem]
    total: int


class ReportRunRequest(BaseModel):
    """Request payload to execute a report view on screen."""

    filters: dict[str, Any] = Field(default_factory=dict)
    page: int = 1
    page_size: int = 50
    sort: dict[str, Any] | None = None


class ReportRunResponse(BaseModel):
    """Response returned when executing a report."""

    meta: dict[str, Any]
    summary: dict[str, Any]
    columns: list[ReportColumn]
    rows: list[dict[str, Any]]
    total: int
    page: int = 1
    page_size: int = 50


class ReportExportRequest(BaseModel):
    """Request payload to export report as XLSX or PDF."""

    filters: dict[str, Any] = Field(default_factory=dict)

