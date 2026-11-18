"""Metric Handler: New Doctor Visits (TABLE)."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

from sqlalchemy.orm import selectinload

from app.modules.customers.models import Doctor
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse


class NewDoctorVisitsMetric(BaseMetricHandler):
    key = "new_doctor_visits"
    title = "New Doctor Visits"
    kind = "TABLE"
    color_group = "primary"

    def _get_base_query(self, ctx: MetricHandlerContext):
        start_dt = datetime.combine(ctx.from_date, time.min)
        end_dt = datetime.combine(ctx.to_date, time.max)
        return (
            ctx.db.query(Doctor)
            .filter(
                Doctor.created_by == ctx.employee.id,
                Doctor.created_at >= start_dt,
                Doctor.created_at <= end_dt,
            )
        )

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        count = self._get_base_query(ctx).count()
        return count, str(count)

    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        query = self._get_base_query(ctx)
        total = query.count()

        columns = [
            MetricColumnItem(key="date", label="Created Date", type="date"),
            MetricColumnItem(key="name", label="Doctor Name", type="string"),
            MetricColumnItem(key="speciality", label="Speciality", type="string"),
            MetricColumnItem(key="mobile", label="Mobile", type="string"),
            MetricColumnItem(key="city", label="City", type="string"),
            MetricColumnItem(key="area", label="Area", type="string"),
            MetricColumnItem(key="approval_status", label="Approval Status", type="status"),
            MetricColumnItem(key="address", label="Clinic Address", type="string"),
        ]

        doctors = (
            query.options(selectinload(Doctor.area))
            .order_by(Doctor.created_at.desc())
            .offset((ctx.page - 1) * ctx.page_size)
            .limit(ctx.page_size)
            .all()
        )

        rows = []
        for d in doctors:
            approval = getattr(d, "approval_status", "APPROVED") or "APPROVED"
            area_name = d.area.name if d.area else (d.city or "-")
            spec = getattr(d, "specialization", None) or getattr(d, "speciality", "-")
            rows.append({
                "id": str(d.id),
                "date": d.created_at.strftime("%Y-%m-%d") if d.created_at else "-",
                "name": f"Dr. {d.full_name}",
                "speciality": spec or "-",
                "mobile": d.phone or "-",
                "city": d.city or "-",
                "area": area_name,
                "approval_status": approval,
                "address": d.address or "-",
            })

        return MetricDetailResponse(
            meta=self.build_meta(ctx, columns),
            rows=rows,
            total=total,
            page=ctx.page,
            page_size=ctx.page_size,
        )
