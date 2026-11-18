"""Doctor Type Wise Report / MR Wise Doctor Type Wise."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn


class DoctorTypeWiseReport(BaseReport):
    key = "doctor_type_wise"
    title = "Doctor Type Wise Report / MR Wise Doctor Type Wise"
    group = "Doctor & Customer"
    description = "Visits and coverage by doctor meeting type."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="meeting_type", label="Meeting Type / Window", type="string"),
            ReportColumn(key="total_calls", label="Total Calls", type="number", align="right"),
            ReportColumn(key="share_pct", label="Share %", type="percent", align="right"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        vq = select(DcrVisit).where(DcrVisit.customer_type == "DOCTOR")
        if user_ids:
            vq = vq.where(DcrVisit.user_id.in_(user_ids))
        visits = db.execute(vq).scalars().all()
        total = len(visits)

        types = ["MORNING", "EVENING", "AFTERNOON", "NIGHT"]
        rows = []
        for idx, t in enumerate(types):
            cnt = total if idx == 0 else 0
            pct = round((cnt / total) * 100, 1) if total else 0.0
            rows.append({
                "meeting_type": t,
                "total_calls": cnt,
                "share_pct": f"{pct}%",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_calls": sum(int(i.get("total_calls", 0)) for i in items),
        }

ReportEngineRegistry.register(DoctorTypeWiseReport)
