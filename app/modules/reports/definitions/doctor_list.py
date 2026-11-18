"""Doctor List Master Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Doctor
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.territories.models import Territory


class DoctorListReport(BaseReport):
    key = "doctor_list"
    title = "Doctor List"
    group = "Doctor & Customer"
    description = "Doctor master listing with contact details, specialities, and territories."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="code", label="Doctor Code", type="string", align="center"),
            ReportColumn(key="name", label="Doctor Name", type="string"),
            ReportColumn(key="speciality", label="Specialization", type="string"),
            ReportColumn(key="qualification", label="Qualification", type="string"),
            ReportColumn(key="category", label="Category", type="string", align="center"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="phone", label="Phone", type="string"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        docs = db.execute(select(Doctor)).scalars().all()
        t_cache = {t.id: t.name for t in db.execute(select(Territory)).scalars().all()}
        rows = []
        for d in docs:
            rows.append({
                "code": d.code,
                "name": d.full_name,
                "speciality": d.specialization or "General",
                "qualification": d.qualification or "MBBS",
                "category": d.category or "A",
                "territory": t_cache.get(d.territory_id, "Central"),
                "phone": d.phone or "-",
                "status": "ACTIVE" if d.is_active else "INACTIVE",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_doctors": len(items),
            "active_doctors": sum(1 for i in items if i.get("status") == "ACTIVE"),
        }

ReportEngineRegistry.register(DoctorListReport)
