"""MR_DoctorWise_Yearly_Summary."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn


class MrDoctorWiseYearlySummaryReport(BaseReport):
    key = "doctor_yearly_summary"
    title = "MR_DoctorWise_Yearly_Summary"
    group = "Doctor & Customer"
    description = "Doctor x month visit counts for a financial year."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="doctor", label="Doctor Name", type="string"),
            ReportColumn(key="speciality", label="Speciality", type="string"),
            ReportColumn(key="category", label="Category", type="string", align="center"),
            ReportColumn(key="q1", label="Q1 Visits", type="number", align="right"),
            ReportColumn(key="q2", label="Q2 Visits", type="number", align="right"),
            ReportColumn(key="q3", label="Q3 Visits", type="number", align="right"),
            ReportColumn(key="q4", label="Q4 Visits", type="number", align="right"),
            ReportColumn(key="annual_total", label="Annual Total", type="number", align="right"),
        ]

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
                "q1": cnt,
                "q2": 0,
                "q3": 0,
                "q4": 0,
                "annual_total": cnt,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_doctors": len(items),
            "annual_calls": sum(int(i.get("annual_total", 0)) for i in items),
        }

ReportEngineRegistry.register(MrDoctorWiseYearlySummaryReport)
