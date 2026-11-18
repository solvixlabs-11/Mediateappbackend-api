"""MR_Wise_Visits_Analysis."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class MrWiseVisitsAnalysisReport(BaseReport):
    key = "mr_visits_analysis"
    title = "MR_Wise_Visits_Analysis"
    group = "Field Activity"
    description = "Visits split by customer type, averages, verified %."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="total_visits", label="Total Visits", type="number", align="right"),
            ReportColumn(key="doctor_visits", label="Doctor Visits", type="number", align="right"),
            ReportColumn(key="chemist_visits", label="Chemist Visits", type="number", align="right"),
            ReportColumn(key="stockist_visits", label="Stockist / Hospital", type="number", align="right"),
            ReportColumn(key="verified_visits", label="Verified Visits", type="number", align="right"),
            ReportColumn(key="verified_pct", label="Verified %", type="percent", align="right"),
            ReportColumn(key="pob_total", label="Total POB (₹)", type="currency", align="right"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users_q = select(User).where(User.is_active == True)
        if user_ids:
            users_q = users_q.where(User.id.in_(user_ids))
        users = db.execute(users_q).scalars().all()

        rows = []
        for u in users:
            vq = select(DcrVisit).where(DcrVisit.user_id == u.id)
            if start_utc and end_utc:
                vq = vq.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)
            visits = db.execute(vq).scalars().all()
            total = len(visits)
            doc_c = sum(1 for v in visits if v.customer_type == "DOCTOR")
            chm_c = sum(1 for v in visits if v.customer_type == "CHEMIST")
            stk_c = sum(1 for v in visits if v.customer_type in ("STOCKIST", "HOSPITAL"))
            ver_c = sum(1 for v in visits if v.is_geofence_verified)
            pob = sum(float(v.pob_amount or 0.0) for v in visits)
            pct = round((ver_c / total) * 100, 1) if total else 0.0

            rows.append({
                "employee": u.full_name,
                "total_visits": total,
                "doctor_visits": doc_c,
                "chemist_visits": chm_c,
                "stockist_visits": stk_c,
                "verified_visits": ver_c,
                "verified_pct": f"{pct}%",
                "pob_total": round(pob, 2),
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot_v = sum(int(i.get("total_visits", 0)) for i in items)
        tot_ver = sum(int(i.get("verified_visits", 0)) for i in items)
        tot_pob = sum(float(i.get("pob_total", 0.0)) for i in items)
        overall_pct = round((tot_ver / tot_v) * 100, 1) if tot_v else 0.0
        return {
            "total_visits": tot_v,
            "overall_verified_pct": f"{overall_pct}%",
            "total_pob_collected": round(tot_pob, 2),
        }

ReportEngineRegistry.register(MrWiseVisitsAnalysisReport)
