"""MR_Deviation_Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dcr.models import DcrVisit, PlannedVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class MrDeviationReport(BaseReport):
    key = "deviation_report"
    title = "MR_Deviation_Report"
    group = "Field Activity"
    description = "Planned versus actual (outside tour plan, unplanned, missed)."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="deviation_type", label="Deviation Type", type="status", align="center"),
            ReportColumn(key="planned", label="Planned Visits", type="number", align="right"),
            ReportColumn(key="completed", label="Completed", type="number", align="right"),
            ReportColumn(key="adherence_pct", label="Adherence %", type="percent", align="right"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users_q = select(User).where(User.is_active == True)
        if user_ids:
            users_q = users_q.where(User.id.in_(user_ids))
        users = db.execute(users_q).scalars().all()

        rows = []
        for u in users:
            pv_cnt = len(db.execute(select(PlannedVisit).where(PlannedVisit.user_id == u.id)).scalars().all())
            dv_cnt = len(db.execute(select(DcrVisit).where(DcrVisit.user_id == u.id)).scalars().all())
            adh = round((dv_cnt / pv_cnt) * 100, 1) if pv_cnt else 100.0
            dev_type = "NORMAL" if adh >= 80 else ("MODERATE_DEVIATION" if adh >= 50 else "HIGH_DEVIATION")

            rows.append({
                "date": datetime.utcnow().date().isoformat(),
                "employee": u.full_name,
                "deviation_type": dev_type,
                "planned": pv_cnt,
                "completed": dv_cnt,
                "adherence_pct": f"{adh}%",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_evaluated": len(items),
            "normal_adherence_count": sum(1 for i in items if i.get("deviation_type") == "NORMAL"),
        }

ReportEngineRegistry.register(MrDeviationReport)
