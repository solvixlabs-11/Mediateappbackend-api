"""Visit Analysis (employee tracker)."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class VisitAnalysisReport(BaseReport):
    key = "visit_analysis"
    title = "Visit Analysis (employee tracker)"
    group = "Specialty & Corporate"
    description = "Per employee visit analysis and field engagement tracker."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="emp_code", label="Emp Code", type="string", align="center"),
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="calls_done", label="Total Calls", type="number", align="right"),
            ReportColumn(key="verified_calls", label="Verified Calls", type="number", align="right"),
            ReportColumn(key="verified_pct", label="Verified %", type="percent", align="right"),
            ReportColumn(key="pob_total", label="Total POB (₹)", type="currency", align="right"),
            ReportColumn(key="productivity_index", label="Productivity Index", type="string", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users_q = select(User).where(User.is_active == True)
        if user_ids:
            users_q = users_q.where(User.id.in_(user_ids))
        users = db.execute(users_q).scalars().all()

        rows = []
        for u in users:
            visits = db.execute(select(DcrVisit).where(DcrVisit.user_id == u.id)).scalars().all()
            tot = len(visits)
            ver = sum(1 for v in visits if v.is_geofence_verified)
            pob = sum(float(v.pob_amount or 0.0) for v in visits)
            pct = round((ver / tot) * 100, 1) if tot else 0.0
            idx = "HIGH" if tot >= 10 else ("MEDIUM" if tot >= 5 else "LOW")

            rows.append({
                "employee": u.full_name,
                "emp_code": u.employee_code,
                "designation": getattr(u, "designation", "MR") or "MR",
                "calls_done": tot,
                "verified_calls": ver,
                "verified_pct": f"{pct}%",
                "pob_total": round(pob, 2),
                "productivity_index": idx,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_employees_tracked": len(items),
            "total_calls_analyzed": sum(int(i.get("calls_done", 0)) for i in items),
            "total_pob_generated": round(sum(float(i.get("pob_total", 0.0)) for i in items), 2),
        }

ReportEngineRegistry.register(VisitAnalysisReport)
