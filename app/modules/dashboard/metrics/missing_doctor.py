"""Metric Handler: Missing Doctor (TABLE)."""

from __future__ import annotations

from datetime import date
from typing import Any
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.modules.customers.models import Doctor
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse
from app.modules.dcr.models import DcrVisit
from app.modules.territories.models import UserTerritoryAssignment

settings = get_settings()


class MissingDoctorMetric(BaseMetricHandler):
    key = "missing_doctor"
    title = "Missing Doctor"
    kind = "TABLE"
    color_group = "success"

    def _get_assigned_territory_ids(self, ctx: MetricHandlerContext) -> list[int]:
        assignments = (
            ctx.db.query(UserTerritoryAssignment)
            .filter(
                UserTerritoryAssignment.user_id == ctx.employee.id,
                UserTerritoryAssignment.unassigned_at.is_(None),
            )
            .all()
        )
        return [a.territory_id for a in assignments if a.territory_id]

    def _get_visited_doctor_ids(self, ctx: MetricHandlerContext) -> list[int]:
        visited_query = (
            ctx.db.query(DcrVisit.doctor_id)
            .filter(
                DcrVisit.user_id == ctx.employee.id,
                DcrVisit.customer_type == "DOCTOR",
                DcrVisit.doctor_id.isnot(None),
                DcrVisit.dcr_date >= ctx.from_date,
                DcrVisit.dcr_date <= ctx.to_date,
            )
            .distinct()
            .all()
        )
        return [r[0] for r in visited_query if r[0]]

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        terr_ids = self._get_assigned_territory_ids(ctx)
        visited_ids = self._get_visited_doctor_ids(ctx)

        query = ctx.db.query(func.count(Doctor.id)).filter(Doctor.is_active == True, Doctor.is_deleted == False)  # noqa: E712
        if terr_ids:
            query = query.filter(Doctor.territory_id.in_(terr_ids))
        if visited_ids:
            query = query.filter(Doctor.id.notin_(visited_ids))

        count = query.scalar() or 0
        return count, str(count)

    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        terr_ids = self._get_assigned_territory_ids(ctx)
        visited_ids = self._get_visited_doctor_ids(ctx)

        query = (
            ctx.db.query(Doctor)
            .filter(Doctor.is_active == True, Doctor.is_deleted == False)  # noqa: E712
        )
        if terr_ids:
            query = query.filter(Doctor.territory_id.in_(terr_ids))
        if visited_ids:
            query = query.filter(Doctor.id.notin_(visited_ids))

        total = query.count()

        columns = [
            MetricColumnItem(key="doctor_name", label="Doctor Name", type="string"),
            MetricColumnItem(key="category", label="Category", type="string"),
            MetricColumnItem(key="speciality", label="Speciality", type="string"),
            MetricColumnItem(key="city", label="City", type="string"),
            MetricColumnItem(key="area", label="Area", type="string"),
            MetricColumnItem(key="last_visit_date", label="Last Visit Date", type="date"),
            MetricColumnItem(key="days_since", label="Days Since Last Visit", type="number", align="right"),
            MetricColumnItem(key="status", label="Status", type="status"),
        ]

        doctors = (
            query.options(selectinload(Doctor.area))
            .order_by(Doctor.full_name.asc())
            .offset((ctx.page - 1) * ctx.page_size)
            .limit(ctx.page_size)
            .all()
        )

        doc_ids = [d.id for d in doctors]
        # Query last visit per doctor
        last_visits: dict[int, date] = {}
        if doc_ids:
            lv_query = (
                ctx.db.query(DcrVisit.doctor_id, func.max(DcrVisit.dcr_date))
                .filter(DcrVisit.doctor_id.in_(doc_ids))
                .group_by(DcrVisit.doctor_id)
                .all()
            )
            last_visits = {d_id: max_d for d_id, max_d in lv_query}

        today = date.today()
        rows = []
        for d in doctors:
            lv = last_visits.get(d.id)
            days_since = (today - lv).days if lv else 999
            spec = getattr(d, "specialization", None) or getattr(d, "speciality", "-")
            area_name = d.area.name if d.area else "-"
            rows.append({
                "id": str(d.id),
                "doctor_name": f"Dr. {d.full_name}",
                "category": getattr(d, "category", "-") or "-",
                "speciality": spec or "-",
                "city": area_name,
                "area": area_name,
                "last_visit_date": lv.isoformat() if lv else "Never Visited",
                "days_since": days_since if lv else "-",
                "status": "UNCOVERED",
            })

        return MetricDetailResponse(
            meta=self.build_meta(ctx, columns),
            rows=rows,
            total=total,
            page=ctx.page,
            page_size=ctx.page_size,
        )
