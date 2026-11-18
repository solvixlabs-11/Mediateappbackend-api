"""Tour Plan Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.tours.models import TourProgram
from app.modules.users.models import User


class TourPlanReport(BaseReport):
    key = "tour_plan_report"
    title = "Tour Plan Report"
    group = "Plans & HR"
    description = "Tour plans per employee with routes, dates, and approval status."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="title", label="Plan Title", type="string"),
            ReportColumn(key="from_date", label="Start Date", type="date", align="center"),
            ReportColumn(key="to_date", label="End Date", type="date", align="center"),
            ReportColumn(key="total_days", label="Total Days", type="number", align="right"),
            ReportColumn(key="routes", label="Route Details", type="string"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        q = select(TourProgram)
        if user_ids:
            q = q.where(TourProgram.user_id.in_(user_ids))
        tps = db.execute(q).scalars().all()
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}

        rows = []
        for tp in tps:
            u = user_cache.get(tp.user_id)
            rows.append({
                "employee": u.full_name if u else f"User #{tp.user_id}",
                "title": tp.title,
                "from_date": tp.start_date.isoformat(),
                "to_date": tp.end_date.isoformat(),
                "total_days": tp.total_days,
                "routes": tp.route_details or "-",
                "status": tp.status,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_tour_plans": len(items),
            "approved_plans": sum(1 for i in items if i.get("status") == "APPROVED"),
            "submitted_plans": sum(1 for i in items if i.get("status") == "SUBMITTED"),
        }

ReportEngineRegistry.register(TourPlanReport)
