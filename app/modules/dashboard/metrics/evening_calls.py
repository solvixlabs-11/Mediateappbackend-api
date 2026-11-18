"""Metric Handler: Evening Calls (TABLE)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse
from app.modules.dcr.models import DcrVisit

settings = get_settings()


class EveningCallsMetric(BaseMetricHandler):
    key = "evening_calls"
    title = "Evening Calls"
    kind = "TABLE"
    color_group = "primary"

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        visits = (
            ctx.db.query(DcrVisit)
            .filter(
                DcrVisit.user_id == ctx.employee.id,
                DcrVisit.dcr_date >= ctx.from_date,
                DcrVisit.dcr_date <= ctx.to_date,
                DcrVisit.call_time.isnot(None),
            )
            .all()
        )
        cutoff = getattr(settings, "VISITS_MORNING_CUTOFF_HOUR", 14)
        count = sum(1 for v in visits if v.call_time and v.call_time.hour >= cutoff)
        return count, str(count)

    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        visits_all = (
            ctx.db.query(DcrVisit)
            .options(
                selectinload(DcrVisit.doctor),
                selectinload(DcrVisit.chemist),
                selectinload(DcrVisit.hospital),
                selectinload(DcrVisit.stockist),
            )
            .filter(
                DcrVisit.user_id == ctx.employee.id,
                DcrVisit.dcr_date >= ctx.from_date,
                DcrVisit.dcr_date <= ctx.to_date,
                DcrVisit.call_time.isnot(None),
            )
            .order_by(DcrVisit.dcr_date.desc(), DcrVisit.call_time.desc())
            .all()
        )

        cutoff = getattr(settings, "VISITS_MORNING_CUTOFF_HOUR", 14)
        filtered = [v for v in visits_all if v.call_time and v.call_time.hour >= cutoff]
        total = len(filtered)

        columns = [
            MetricColumnItem(key="date", label="Date", type="date"),
            MetricColumnItem(key="time", label="Call Time", type="time"),
            MetricColumnItem(key="customer_name", label="Customer Name", type="string"),
            MetricColumnItem(key="customer_type", label="Type", type="string"),
            MetricColumnItem(key="area", label="Area", type="string"),
            MetricColumnItem(key="city", label="City", type="string"),
            MetricColumnItem(key="verified", label="Verified", type="status"),
            MetricColumnItem(key="pob_amount", label="POB Amount", type="currency", align="right"),
        ]

        paged_visits = filtered[(ctx.page - 1) * ctx.page_size : ctx.page * ctx.page_size]

        rows = []
        for v in paged_visits:
            cust_name = "Customer"
            city = "-"
            if v.doctor:
                cust_name = f"Dr. {v.doctor.full_name}"
                city = v.doctor.area.name if getattr(v.doctor, "area", None) else "-"
            elif v.chemist:
                cust_name = v.chemist.shop_name
                city = v.chemist.area.name if getattr(v.chemist, "area", None) else "-"
            elif v.hospital:
                cust_name = v.hospital.name
                city = v.hospital.area.name if getattr(v.hospital, "area", None) else "-"
            elif v.stockist:
                cust_name = v.stockist.agency_name
                city = v.stockist.area.name if getattr(v.stockist, "area", None) else "-"

            rows.append({
                "id": str(v.id),
                "date": v.dcr_date.isoformat() if v.dcr_date else "-",
                "time": v.call_time.strftime("%H:%M") if v.call_time else "-",
                "customer_name": cust_name,
                "customer_type": v.customer_type.title() if v.customer_type else "-",
                "area": city,
                "city": city,
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
