"""MR Wise PromotionalCall."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class MrWisePromotionalCallReport(BaseReport):
    key = "promotional_call"
    title = "MR Wise PromotionalCall"
    group = "Field Activity"
    description = "Calls of the promotional call type."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="doctor", label="Doctor Name", type="string"),
            ReportColumn(key="speciality", label="Speciality", type="string"),
            ReportColumn(key="visit_type", label="Visit Type", type="string", align="center"),
            ReportColumn(key="verified", label="Geofence Verified", type="status", align="center"),
            ReportColumn(key="pob", label="POB Amount (₹)", type="currency", align="right"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        q = select(DcrVisit).where(DcrVisit.customer_type == "DOCTOR")
        if user_ids:
            q = q.where(DcrVisit.user_id.in_(user_ids))
        if start_utc and end_utc:
            q = q.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)

        visits = db.execute(q).scalars().all()
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}
        doc_cache = {d.id: d for d in db.execute(select(Doctor)).scalars().all()}

        rows = []
        for v in visits:
            u = user_cache.get(v.user_id)
            d = doc_cache.get(v.doctor_id) if v.doctor_id else None
            rows.append({
                "date": v.dcr_date.isoformat(),
                "employee": u.full_name if u else f"User #{v.user_id}",
                "doctor": d.full_name if d else "Doctor",
                "speciality": d.specialization if d else "-",
                "visit_type": v.visit_type or "REGULAR SAMPLE CALL",
                "verified": "VERIFIED" if v.is_geofence_verified else "UNVERIFIED",
                "pob": float(v.pob_amount or 0.0),
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_promotional_calls": len(items),
            "total_pob": round(sum(float(i.get("pob", 0.0)) for i in items), 2),
        }

ReportEngineRegistry.register(MrWisePromotionalCallReport)
