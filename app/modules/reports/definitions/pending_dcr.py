"""Pending DCR Details."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.attendance.models import Attendance
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class PendingDcrReport(BaseReport):
    key = "pending_dcr"
    title = "Pending DCR Details"
    group = "Field Activity"
    description = "Days with check-in but missing or late visit reports."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="checkin_time", label="Punch-in Time", type="string", align="center"),
            ReportColumn(key="visits_submitted", label="DCR Calls Logged", type="number", align="right"),
            ReportColumn(key="status", label="Compliance Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        att_q = select(Attendance)
        if user_ids:
            att_q = att_q.where(Attendance.user_id.in_(user_ids))
        records = db.execute(att_q).scalars().all()
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}

        rows = []
        for r in records:
            u = user_cache.get(r.user_id)
            dcr_cnt = len(db.execute(select(DcrVisit).where(DcrVisit.user_id == r.user_id, DcrVisit.dcr_date == r.attendance_date)).scalars().all())
            status = "COMPLIANT" if dcr_cnt > 0 else "PENDING_DCR"

            rows.append({
                "date": r.attendance_date.isoformat(),
                "employee": u.full_name if u else f"User #{r.user_id}",
                "checkin_time": r.check_in_time.strftime("%H:%M") if r.check_in_time else "-",
                "visits_submitted": dcr_cnt,
                "status": status,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        pending_c = sum(1 for i in items if i.get("status") == "PENDING_DCR")
        return {
            "total_checkin_days": len(items),
            "pending_dcr_days": pending_c,
            "compliance_rate": f"{round(((len(items) - pending_c) / len(items)) * 100, 1) if items else 100}%",
        }

ReportEngineRegistry.register(PendingDcrReport)
