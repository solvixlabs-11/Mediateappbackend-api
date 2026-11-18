"""Metric Handler: Doctor Visits (TABLE)."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import selectinload

from app.modules.customers.models import Doctor
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse
from app.modules.dcr.models import DcrVisit


class DoctorVisitsMetric(BaseMetricHandler):
    key = "doctor_visits"
    title = "Doctor Visits"
    kind = "TABLE"
    color_group = "primary"

    def _get_base_query(self, ctx: MetricHandlerContext):
        return (
            ctx.db.query(DcrVisit)
            .filter(
                DcrVisit.user_id == ctx.employee.id,
                DcrVisit.customer_type == "DOCTOR",
                DcrVisit.dcr_date >= ctx.from_date,
                DcrVisit.dcr_date <= ctx.to_date,
            )
        )

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        count = self._get_base_query(ctx).count()
        return count, str(count)

    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        query = self._get_base_query(ctx)
        total = query.count()

        columns = [
            MetricColumnItem(key="date", label="Date", type="date"),
            MetricColumnItem(key="time", label="Time", type="time"),
            MetricColumnItem(key="doctor_name", label="Doctor Name", type="string"),
            MetricColumnItem(key="speciality", label="Speciality", type="string"),
            MetricColumnItem(key="category", label="Category", type="string"),
            MetricColumnItem(key="area", label="Area", type="string"),
            MetricColumnItem(key="city", label="City", type="string"),
            MetricColumnItem(key="visit_type", label="Visit Type", type="string"),
            MetricColumnItem(key="address", label="Address", type="string"),
            MetricColumnItem(key="verified", label="Verified", type="status"),
            MetricColumnItem(key="pob_amount", label="POB Amount", type="currency", align="right"),
        ]

        visits = (
            query.options(
                selectinload(DcrVisit.doctor).joinedload(Doctor.area),
            )
            .order_by(DcrVisit.dcr_date.desc(), DcrVisit.call_time.desc())
            .offset((ctx.page - 1) * ctx.page_size)
            .limit(ctx.page_size)
            .all()
        )

        rows = []
        for v in visits:
            doc = v.doctor
            spec = getattr(doc, "specialization", None) or getattr(doc, "speciality", "-") if doc else "-"
            cat = getattr(doc, "category", "-") if doc else "-"
            area_name = doc.area.name if doc and getattr(doc, "area", None) else "-"
            rows.append({
                "id": str(v.id),
                "date": v.dcr_date.isoformat() if v.dcr_date else "-",
                "time": v.call_time.strftime("%H:%M") if v.call_time else "-",
                "doctor_name": f"Dr. {doc.full_name}" if doc else "Unknown Doctor",
                "speciality": spec or "-",
                "category": cat or "-",
                "area": area_name,
                "city": area_name,
                "visit_type": v.call_type or "Regular",
                "address": doc.address if doc else "-",
                "verified": "VERIFIED" if v.is_geofence_verified else "UNVERIFIED",
                "pob_amount": float(v.pob_amount or 0.0),
            })

        return MetricDetailResponse(
            meta=self.build_meta(ctx, columns),
            rows=rows,
            total=total,
            page=ctx.page,
            page_size=ctx.page_size,
        )
