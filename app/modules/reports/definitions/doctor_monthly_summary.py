"""MR_Doctor_Wise_Monthly_Summary."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn


class MrDoctorWiseMonthlySummaryReport(BaseReport):
    key = "doctor_monthly_summary"
    title = "MR_Doctor_Wise_Monthly_Summary"
    group = "Doctor & Customer"
    description = "Doctor x day visit counts for a month."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        cols = [
            ReportColumn(key="doctor", label="Doctor Name", type="string"),
            ReportColumn(key="speciality", label="Speciality", type="string"),
            ReportColumn(key="category", label="Category", type="string", align="center"),
            ReportColumn(key="total_visits", label="Total Calls", type="number", align="right"),
        ]
        return cols

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        docs = db.execute(select(Doctor)).scalars().all()
        rows = []
        for d in docs:
            vq = select(DcrVisit).where(DcrVisit.doctor_id == d.id)
            if user_ids:
                vq = vq.where(DcrVisit.user_id.in_(user_ids))
            cnt = len(db.execute(vq).scalars().all())
            rows.append({
                "doctor": d.full_name,
                "speciality": d.specialization or "General",
                "category": d.category or "A",
                "total_visits": cnt,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_doctors_evaluated": len(items),
            "doctors_visited": sum(1 for i in items if i.get("total_visits", 0) > 0),
        }

ReportEngineRegistry.register(MrDoctorWiseMonthlySummaryReport)
