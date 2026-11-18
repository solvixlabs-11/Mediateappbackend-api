"""MR_Designation_Wise_Visits_Analysis."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class MrDesignationWiseVisitsAnalysisReport(BaseReport):
    key = "designation_visits_analysis"
    title = "MR_Designation_Wise_Visits_Analysis"
    group = "Field Activity"
    description = "Visits grouped by designation."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="reps_count", label="Total Field Force", type="number", align="right"),
            ReportColumn(key="total_visits", label="Total Calls", type="number", align="right"),
            ReportColumn(key="avg_calls_per_rep", label="Calls / Representative", type="number", align="right"),
            ReportColumn(key="verified_pct", label="Verified %", type="percent", align="right"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users = db.execute(select(User).where(User.is_active == True)).scalars().all()
        by_desig: dict[str, list[User]] = {}
        for u in users:
            d = getattr(u, "designation", "MR") or "MR"
            by_desig.setdefault(d, []).append(u)

        rows = []
        for desig, rep_list in by_desig.items():
            u_ids = [u.id for u in rep_list]
            vq = select(DcrVisit).where(DcrVisit.user_id.in_(u_ids))
            if start_utc and end_utc:
                vq = vq.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)
            visits = db.execute(vq).scalars().all()
            tot_v = len(visits)
            ver_v = sum(1 for v in visits if v.is_geofence_verified)
            avg_v = round(tot_v / len(rep_list), 1) if rep_list else 0.0
            v_pct = round((ver_v / tot_v) * 100, 1) if tot_v else 0.0

            rows.append({
                "designation": desig,
                "reps_count": len(rep_list),
                "total_visits": tot_v,
                "avg_calls_per_rep": avg_v,
                "verified_pct": f"{v_pct}%",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_designations": len(items),
            "total_field_force": sum(int(i.get("reps_count", 0)) for i in items),
            "total_calls": sum(int(i.get("total_visits", 0)) for i in items),
        }

ReportEngineRegistry.register(MrDesignationWiseVisitsAnalysisReport)
