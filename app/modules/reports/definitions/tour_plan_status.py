"""Tour Plan Status Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.tours.models import TourProgram
from app.modules.users.models import User


class TourPlanStatusReport(BaseReport):
    key = "tour_plan_status"
    title = "Tour Plan Status Report"
    group = "Plans & HR"
    description = "Submitted, approved, pending tour plans per employee for a month."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="emp_code", label="Emp Code", type="string", align="center"),
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="status", label="Tour Plan Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users_q = select(User).where(User.is_active == True)
        if user_ids:
            users_q = users_q.where(User.id.in_(user_ids))
        users = db.execute(users_q).scalars().all()
        submitted_user_ids = {tp.user_id for tp in db.execute(select(TourProgram)).scalars().all()}

        rows = []
        for u in users:
            status = "SUBMITTED" if u.id in submitted_user_ids else "NOT_SUBMITTED"
            rows.append({
                "employee": u.full_name,
                "emp_code": u.employee_code,
                "designation": getattr(u, "designation", "MR") or "MR",
                "status": status,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        sub = sum(1 for i in items if i.get("status") == "SUBMITTED")
        return {
            "total_field_reps": len(items),
            "plans_submitted": sub,
            "submission_compliance": f"{round((sub / len(items)) * 100, 1) if items else 0.0}%",
        }

ReportEngineRegistry.register(TourPlanStatusReport)
