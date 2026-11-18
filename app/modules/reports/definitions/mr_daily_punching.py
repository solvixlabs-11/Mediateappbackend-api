"""MR_DailyPunching."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.attendance.models import Attendance
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class MrDailyPunchingReport(BaseReport):
    key = "mr_daily_punching"
    title = "MR_DailyPunching"
    group = "Field Activity"
    description = "Punch in and punch out time and place per day."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="punch_in", label="Punch-in Time & Place", type="string"),
            ReportColumn(key="punch_out", label="Punch-out Time & Place", type="string"),
            ReportColumn(key="hours", label="Hours", type="number", align="right"),
            ReportColumn(key="late", label="Late Status", type="status", align="center"),
            ReportColumn(key="work_type", label="Work Type", type="string", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        q = select(Attendance)
        if user_ids:
            q = q.where(Attendance.user_id.in_(user_ids))
        if start_utc and end_utc:
            q = q.where(Attendance.check_in_time >= start_utc, Attendance.check_in_time <= end_utc)

        records = db.execute(q).scalars().all()
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}
        rows = []
        for r in records:
            u = user_cache.get(r.user_id)
            pin = f"{r.check_in_time.strftime('%H:%M')} ({r.check_in_address or 'Field'})" if r.check_in_time else "-"
            pout = f"{r.check_out_time.strftime('%H:%M')} ({r.check_out_address or 'Field'})" if r.check_out_time else "-"
            hrs = round(float(r.working_hours or 0.0), 1)
            rows.append({
                "date": r.attendance_date.isoformat(),
                "employee": u.full_name if u else f"User #{r.user_id}",
                "punch_in": pin,
                "punch_out": pout,
                "hours": hrs,
                "late": "LATE" if r.is_late else "ON_TIME",
                "work_type": r.work_type or "FIELD",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_p = len(items)
        late_c = sum(1 for i in items if i.get("late") == "LATE")
        avg_h = round(sum(float(i.get("hours", 0)) for i in items) / total_p, 1) if total_p else 0.0
        return {
            "total_punch_ins": total_p,
            "late_count": late_c,
            "on_time_pct": f"{round(((total_p - late_c) / total_p) * 100, 1) if total_p else 100}%",
            "average_working_hours": avg_h,
        }

ReportEngineRegistry.register(MrDailyPunchingReport)
