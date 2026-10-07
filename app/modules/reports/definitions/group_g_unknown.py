"""Group G: Unknown / Special reports (Report 26)."""

from __future__ import annotations

from typing import Any

from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn


class InductionReport(BaseReport):
    """Report 26: Induction Report (ASK - Admin only).

    Status: ASK. Owner must provide sample screen from reference app.
    """

    key = "induction_report"
    title = "Induction Report"
    group = "Other"
    description = "Field staff induction and onboarding status report."
    landscape = False
    allowed_roles = ["ADMIN"]
    report_number = 26
    status = "ASK"
    is_ready = False
    coming_soon_reason = "Awaiting sample output format from the reference application"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR Name", type="string"),
            ReportColumn(key="induction_date", label="Induction Date", type="date", align="center"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


ReportRegistry.register(InductionReport)
