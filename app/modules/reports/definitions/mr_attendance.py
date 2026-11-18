"""MR_Wise_Attendence_Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.attendance.models import Attendance
from app.modules.leaves.models import LeaveRequest
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class MrWiseAttendanceReport(BaseReport):
    key = "mr_attendance"
    title = "MR_Wise_Attendence_Report"
    group = "Field Activity"
    description = "Month matrix P, A, L, W with totals."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="emp_code", label="Emp Code", type="string", align="center"),
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="present_days", label="Present (P)", type="number", align="right"),
            ReportColumn(key="absent_days", label="Absent (A)", type="number", align="right"),
            ReportColumn(key="leave_days", label="Leave (L)", type="number", align="right"),
            ReportColumn(key="weekly_offs", label="Weekly Off (W)", type="number", align="right"),
            ReportColumn(key="attendance_pct", label="Attendance %", type="percent", align="right"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users_q = select(User).where(User.is_active == True)
        if user_ids:
            users_q = users_q.where(User.id.in_(user_ids))
        users = db.execute(users_q).scalars().all()

        rows = []
        for u in users:
            # Query attendance count
            p_cnt = len(db.execute(select(Attendance).where(Attendance.user_id == u.id)).scalars().all())
            l_cnt = len(db.execute(select(LeaveRequest).where(LeaveRequest.user_id == u.id, LeaveRequest.status == "APPROVED")).scalars().all())
            w_cnt = 4
            working_days = 26
            a_cnt = max(0, working_days - (p_cnt + l_cnt))
            pct = round((p_cnt / working_days) * 100, 1) if working_days else 0.0

            rows.append({
                "employee": u.full_name,
                "emp_code": u.employee_code,
                "designation": getattr(u, "designation", "MR") or "MR",
                "present_days": p_cnt,
                "absent_days": a_cnt,
                "leave_days": l_cnt,
                "weekly_offs": w_cnt,
                "attendance_pct": f"{pct}%",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_p = sum(int(i.get("present_days", 0)) for i in items)
        total_l = sum(int(i.get("leave_days", 0)) for i in items)
        return {
            "total_employees": len(items),
            "total_present_days": total_p,
            "total_leave_days": total_l,
        }

ReportEngineRegistry.register(MrWiseAttendanceReport)
