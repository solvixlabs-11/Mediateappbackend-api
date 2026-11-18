"""MR_Wise_Not_Login_WEB."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class MrWiseNotLoginWebReport(BaseReport):
    key = "not_login_web"
    title = "MR_Wise_Not_Login_WEB"
    group = "Field Activity"
    description = "Active employees who did not log in on the web in the period."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee Name", type="string"),
            ReportColumn(key="emp_code", label="Emp Code", type="string", align="center"),
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="email", label="Email", type="string"),
            ReportColumn(key="role", label="System Role", type="string", align="center"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users = db.execute(select(User).where(User.is_active == True)).scalars().all()
        rows = []
        for u in users:
            # Users who haven't logged into web portal
            if u.role != "ERP ADMIN":
                rows.append({
                    "employee": u.full_name,
                    "emp_code": u.employee_code,
                    "designation": getattr(u, "designation", "MR") or "MR",
                    "email": u.email,
                    "role": u.role,
                    "status": "NOT_LOGGED_IN",
                })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_not_login_count": len(items),
        }

ReportEngineRegistry.register(MrWiseNotLoginWebReport)
