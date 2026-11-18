"""MR Wise Route Master."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Chemist, Doctor
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.territories.models import Territory
from app.modules.users.models import User


class RouteMasterReport(BaseReport):
    key = "route_master"
    title = "MR Wise Route Master"
    group = "Doctor & Customer"
    description = "Territory or route assignment per employee."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="territory", label="Route / Territory", type="string"),
            ReportColumn(key="doctors", label="Mapped Doctors", type="number", align="right"),
            ReportColumn(key="chemists", label="Mapped Chemists", type="number", align="right"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users_q = select(User).where(User.is_active == True)
        if user_ids:
            users_q = users_q.where(User.id.in_(user_ids))
        users = db.execute(users_q).scalars().all()
        t_cache = {t.id: t.name for t in db.execute(select(Territory)).scalars().all()}

        rows = []
        for u in users:
            t_name = t_cache.get(u.territory_id, "Central HQ")
            docs = len(db.execute(select(Doctor).where(Doctor.territory_id == u.territory_id)).scalars().all()) if u.territory_id else 0
            chms = len(db.execute(select(Chemist).where(Chemist.territory_id == u.territory_id)).scalars().all()) if u.territory_id else 0

            rows.append({
                "employee": u.full_name,
                "designation": getattr(u, "designation", "MR") or "MR",
                "territory": t_name,
                "doctors": docs,
                "chemists": chms,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_assigned_reps": len(items),
            "total_mapped_doctors": sum(int(i.get("doctors", 0)) for i in items),
        }

ReportEngineRegistry.register(RouteMasterReport)
