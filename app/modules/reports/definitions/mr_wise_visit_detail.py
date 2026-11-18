"""MR Wise Visit Detail / MR Wise Visits."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Chemist, Doctor, Hospital, Stockist
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class MrWiseVisitDetailReport(BaseReport):
    key = "mr_wise_visit_detail"
    title = "MR Wise Visit Detail / MR Wise Visits"
    group = "Field Activity"
    description = "Every visit with its details, grouped by employee and date."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="time", label="Call Time", type="string", align="center"),
            ReportColumn(key="customer_name", label="Customer Name", type="string"),
            ReportColumn(key="customer_type", label="Type", type="string", align="center"),
            ReportColumn(key="speciality", label="Speciality / Details", type="string"),
            ReportColumn(key="verified", label="Geofence Verified", type="status", align="center"),
            ReportColumn(key="pob_amount", label="POB Amount (₹)", type="currency", align="right"),
            ReportColumn(key="remarks", label="Remarks", type="string"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        q = select(DcrVisit)
        if user_ids:
            q = q.where(DcrVisit.user_id.in_(user_ids))
        if start_utc and end_utc:
            q = q.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)

        visits = db.execute(q).scalars().all()
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}
        doc_cache = {d.id: d for d in db.execute(select(Doctor)).scalars().all()}
        chm_cache = {c.id: c for c in db.execute(select(Chemist)).scalars().all()}
        stk_cache = {s.id: s for s in db.execute(select(Stockist)).scalars().all()}
        hosp_cache = {h.id: h for h in db.execute(select(Hospital)).scalars().all()}

        rows = []
        for v in visits:
            u = user_cache.get(v.user_id)
            c_name = "Unknown Customer"
            spec = "-"
            if v.customer_type == "DOCTOR" and v.doctor_id in doc_cache:
                doc = doc_cache[v.doctor_id]
                c_name = doc.full_name
                spec = f"{doc.specialization or ''} ({doc.category or 'A'})"
            elif v.customer_type == "CHEMIST" and v.chemist_id in chm_cache:
                c_name = chm_cache[v.chemist_id].shop_name
            elif v.customer_type == "STOCKIST" and v.stockist_id in stk_cache:
                c_name = stk_cache[v.stockist_id].agency_name
            elif v.customer_type == "HOSPITAL" and v.hospital_id in hosp_cache:
                c_name = hosp_cache[v.hospital_id].name

            rows.append({
                "date": v.dcr_date.isoformat(),
                "employee": u.full_name if u else f"User #{v.user_id}",
                "time": v.call_time.strftime("%H:%M") if v.call_time else "-",
                "customer_name": c_name,
                "customer_type": v.customer_type,
                "speciality": spec,
                "verified": "VERIFIED" if v.is_geofence_verified else "UNVERIFIED",
                "pob_amount": float(v.pob_amount or 0.0),
                "remarks": v.remarks or "-",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_pob = sum(float(i.get("pob_amount", 0.0)) for i in items)
        verified_cnt = sum(1 for i in items if i.get("verified") == "VERIFIED")
        v_pct = round((verified_cnt / len(items)) * 100, 1) if items else 0.0
        return {
            "total_visits": len(items),
            "verified_percentage": f"{v_pct}%",
            "total_pob_amount": round(total_pob, 2),
        }

ReportEngineRegistry.register(MrWiseVisitDetailReport)
