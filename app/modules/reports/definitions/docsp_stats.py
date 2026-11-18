"""MR Wise DocSp Wise Stats."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn


class MrWiseDocSpWiseStatsReport(BaseReport):
    key = "docsp_stats"
    title = "MR Wise DocSp Wise Stats"
    group = "Doctor & Customer"
    description = "Specialization wise doctors, visits, coverage."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="speciality", label="Speciality", type="string"),
            ReportColumn(key="total_doctors", label="Doctor Count", type="number", align="right"),
            ReportColumn(key="visited_doctors", label="Doctors Visited", type="number", align="right"),
            ReportColumn(key="total_visits", label="Total Calls", type="number", align="right"),
            ReportColumn(key="coverage_pct", label="Coverage %", type="percent", align="right"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        docs = db.execute(select(Doctor)).scalars().all()
        by_sp: dict[str, list[Doctor]] = {}
        for d in docs:
            sp = d.specialization or "General Medicine"
            by_sp.setdefault(sp, []).append(d)

        rows = []
        for sp, doc_list in by_sp.items():
            d_ids = [d.id for d in doc_list]
            visits = db.execute(select(DcrVisit).where(DcrVisit.doctor_id.in_(d_ids))).scalars().all()
            visited_set = {v.doctor_id for v in visits}
            cov = round((len(visited_set) / len(doc_list)) * 100, 1) if doc_list else 0.0

            rows.append({
                "speciality": sp,
                "total_doctors": len(doc_list),
                "visited_doctors": len(visited_set),
                "total_visits": len(visits),
                "coverage_pct": f"{cov}%",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_specialities": len(items),
            "total_doctors": sum(int(i.get("total_doctors", 0)) for i in items),
        }

ReportEngineRegistry.register(MrWiseDocSpWiseStatsReport)
