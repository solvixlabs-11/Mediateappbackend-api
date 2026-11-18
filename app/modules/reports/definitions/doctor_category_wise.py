"""MR Wise Doctor Category Wise Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn


class MrWiseDoctorCategoryWiseReport(BaseReport):
    key = "doctor_category_wise"
    title = "MR Wise Doctor Category Wise Report"
    group = "Doctor & Customer"
    description = "Category wise assigned, visited, coverage."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="category", label="Category", type="string", align="center"),
            ReportColumn(key="total_doctors", label="Doctor Count", type="number", align="right"),
            ReportColumn(key="visited_doctors", label="Visited Doctors", type="number", align="right"),
            ReportColumn(key="total_visits", label="Total Calls", type="number", align="right"),
            ReportColumn(key="coverage_pct", label="Coverage %", type="percent", align="right"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        docs = db.execute(select(Doctor)).scalars().all()
        by_cat: dict[str, list[Doctor]] = {}
        for d in docs:
            cat = d.category or "A"
            by_cat.setdefault(cat, []).append(d)

        rows = []
        for cat, doc_list in by_cat.items():
            d_ids = [d.id for d in doc_list]
            visits = db.execute(select(DcrVisit).where(DcrVisit.doctor_id.in_(d_ids))).scalars().all()
            visited_set = {v.doctor_id for v in visits}
            cov = round((len(visited_set) / len(doc_list)) * 100, 1) if doc_list else 0.0

            rows.append({
                "category": cat,
                "total_doctors": len(doc_list),
                "visited_doctors": len(visited_set),
                "total_visits": len(visits),
                "coverage_pct": f"{cov}%",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_categories": len(items),
            "total_doctors": sum(int(i.get("total_doctors", 0)) for i in items),
        }

ReportEngineRegistry.register(MrWiseDoctorCategoryWiseReport)
