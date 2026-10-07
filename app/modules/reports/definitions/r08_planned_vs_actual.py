"""R08 - Planned vs Actual Report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.dcr.models import DcrVisit, PlannedVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.users.models import User


class PlannedVsActualReport(BaseReport):
    """R08 Planned vs Actual.

    Planned, completed, missed, cancelled, unplanned visits, adherence %.
    """

    key = "planned_vs_actual"
    title = "Planned vs Actual Report"
    group = "Activity"
    description = "Pre-call planned schedule vs field execution, completed, missed, cancelled, and tour adherence %."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="planned", label="Planned", type="number", align="right"),
            ReportColumn(key="completed", label="Completed", type="number", align="right"),
            ReportColumn(key="missed", label="Missed", type="number", align="right"),
            ReportColumn(key="cancelled", label="Cancelled", type="number", align="right"),
            ReportColumn(key="unplanned", label="Unplanned", type="number", align="right"),
            ReportColumn(key="adherence_pct", label="Adherence %", type="percent", align="right"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        p_stmt = (
            select(
                PlannedVisit.plan_date,
                PlannedVisit.user_id,
                User.full_name,
                func.count(PlannedVisit.id),
                func.sum(func.case((PlannedVisit.status == "COMPLETED", 1), else_=0)),
                func.sum(func.case((PlannedVisit.status == "MISSED", 1), else_=0)),
                func.sum(func.case((PlannedVisit.status == "CANCELLED", 1), else_=0)),
            )
            .join(User, PlannedVisit.user_id == User.id)
            .group_by(PlannedVisit.plan_date, PlannedVisit.user_id, User.full_name)
            .order_by(PlannedVisit.plan_date.desc(), User.full_name)
        )

        if user_ids is not None:
            p_stmt = p_stmt.where(PlannedVisit.user_id.in_(user_ids))
        if start_utc and end_utc:
            p_stmt = p_stmt.where(
                PlannedVisit.created_at >= start_utc,
                PlannedVisit.created_at <= end_utc,
            )

        rows = db.execute(p_stmt).all()
        results: list[dict[str, Any]] = []

        for p_date, u_id, u_name, total_p, comp_p, miss_p, canc_p in rows:
            p_val = int(total_p or 0)
            c_val = int(comp_p or 0)
            m_val = int(miss_p or 0)
            can_val = int(canc_p or 0)

            # Unplanned visits executed on that date
            unp_stmt = select(func.count(DcrVisit.id)).where(
                DcrVisit.user_id == u_id,
                DcrVisit.dcr_date == p_date,
                DcrVisit.planned_visit_id.is_(None),
            )
            unp_val = int(db.scalar(unp_stmt) or 0)

            adh = round((c_val / p_val * 100.0), 1) if p_val > 0 else 100.0

            results.append(
                {
                    "date": p_date.isoformat(),
                    "mr_name": u_name,
                    "planned": p_val,
                    "completed": c_val,
                    "missed": m_val,
                    "cancelled": can_val,
                    "unplanned": unp_val,
                    "adherence_pct": f"{adh}%",
                    "_raw_planned": p_val,
                    "_raw_completed": c_val,
                }
            )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot_planned = sum(int(it.get("_raw_planned", 0)) for it in items)
        tot_completed = sum(int(it.get("_raw_completed", 0)) for it in items)
        adh = round(tot_completed / tot_planned * 100.0, 1) if tot_planned > 0 else 0.0

        return {
            "total_planned": tot_planned,
            "total_completed": tot_completed,
            "overall_adherence_pct": adh,
        }


ReportRegistry.register(PlannedVsActualReport)
