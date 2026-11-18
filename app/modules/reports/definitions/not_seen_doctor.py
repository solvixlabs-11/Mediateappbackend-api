"""MR_Wise_Not_Seen_Doctor."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.territories.models import Territory


class MrWiseNotSeenDoctorReport(BaseReport):
    key = "not_seen_doctor"
    title = "MR_Wise_Not_Seen_Doctor"
    group = "Doctor & Customer"
    description = "Doctors not visited in the period."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="doctor", label="Doctor Name", type="string"),
            ReportColumn(key="speciality", label="Speciality", type="string"),
            ReportColumn(key="category", label="Category", type="string", align="center"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="status", label="Coverage Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        docs = db.execute(select(Doctor)).scalars().all()
        t_cache = {t.id: t.name for t in db.execute(select(Territory)).scalars().all()}
        visited_ids = set(db.execute(select(DcrVisit.doctor_id).where(DcrVisit.doctor_id.isnot(None))).scalars().all())

        rows = []
        for d in docs:
            if d.id not in visited_ids:
                rows.append({
                    "doctor": d.full_name,
                    "speciality": d.specialization or "General",
                    "category": d.category or "A",
                    "territory": t_cache.get(d.territory_id, "Central"),
                    "status": "NOT_VISITED",
                })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "unvisited_doctors_count": len(items),
        }

ReportEngineRegistry.register(MrWiseNotSeenDoctorReport)
