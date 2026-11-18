"""Unassigned_MR_Division_Wise_Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class UnassignedMrDivisionReport(BaseReport):
    key = "unassigned_mr_division"
    title = "Unassigned_MR_Division_Wise_Report"
    group = "Doctor & Customer"
    description = "Employees not mapped to a division."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="emp_code", label="Emp Code", type="string", align="center"),
            ReportColumn(key="role", label="Role", type="string", align="center"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        # Check users without division
        users = db.execute(select(User).where(User.is_active == True)).scalars().all()
        rows = []
        for u in users:
            if not getattr(u, "division_id", None):
                rows.append({
                    "employee": u.full_name,
                    "emp_code": u.employee_code,
                    "role": u.role,
                    "status": "UNMAPPED_DIVISION",
                })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "unmapped_division_count": len(items),
        }

ReportEngineRegistry.register(UnassignedMrDivisionReport)
