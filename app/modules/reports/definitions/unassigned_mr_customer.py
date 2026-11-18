"""Unassigned_MR_Customer_Wise_Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class UnassignedMrCustomerReport(BaseReport):
    key = "unassigned_mr_customer"
    title = "Unassigned_MR_Customer_Wise_Report"
    group = "Doctor & Customer"
    description = "Employees with no customers assigned."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="emp_code", label="Emp Code", type="string", align="center"),
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="status", label="Mapping Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users = db.execute(select(User).where(User.territory_id.is_(None), User.role == "MR")).scalars().all()
        rows = []
        for u in users:
            rows.append({
                "employee": u.full_name,
                "emp_code": u.employee_code,
                "designation": getattr(u, "designation", "MR") or "MR",
                "status": "NO_CUSTOMERS",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "unassigned_reps_count": len(items),
        }

ReportEngineRegistry.register(UnassignedMrCustomerReport)
