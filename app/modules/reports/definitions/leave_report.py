"""MR_Wise_Leave_Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.leaves.models import LeaveRequest
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class LeaveReport(BaseReport):
    key = "leave_report"
    title = "MR_Wise_Leave_Report"
    group = "Plans & HR"
    description = "Leaves per employee with balances and approval trail."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="leave_type", label="Leave Type", type="string", align="center"),
            ReportColumn(key="from_date", label="From Date", type="date", align="center"),
            ReportColumn(key="to_date", label="To Date", type="date", align="center"),
            ReportColumn(key="days", label="Days Count", type="number", align="right"),
            ReportColumn(key="reason", label="Reason", type="string"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        q = select(LeaveRequest)
        if user_ids:
            q = q.where(LeaveRequest.user_id.in_(user_ids))
        leaves = db.execute(q).scalars().all()
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}

        rows = []
        for lr in leaves:
            u = user_cache.get(lr.user_id)
            rows.append({
                "employee": u.full_name if u else f"User #{lr.user_id}",
                "leave_type": lr.leave_type,
                "from_date": lr.start_date.isoformat(),
                "to_date": lr.end_date.isoformat(),
                "days": lr.days_count,
                "reason": lr.reason,
                "status": lr.status,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_leave_requests": len(items),
            "approved_leaves": sum(1 for i in items if i.get("status") == "APPROVED"),
            "pending_leaves": sum(1 for i in items if i.get("status") == "PENDING"),
        }

ReportEngineRegistry.register(LeaveReport)
