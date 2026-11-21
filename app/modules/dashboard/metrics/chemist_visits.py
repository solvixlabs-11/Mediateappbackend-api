"""Metric Handler: Chemist Visits (TABLE)."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import selectinload

from app.modules.customers.models import Chemist
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse
from app.modules.dcr.models import DcrVisit


class ChemistVisitsMetric(BaseMetricHandler):
    key = "chemist_visits"
    title = "Chemist Visits"
    kind = "TABLE"
    color_group = "primary"

    def _get_base_query(self, ctx: MetricHandlerContext):
        return (
            ctx.db.query(DcrVisit)
            .filter(
                DcrVisit.user_id == ctx.employee.id,
                DcrVisit.customer_type == "CHEMIST",
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
            MetricColumnItem(key="chemist_name", label="Chemist Name", type="string"),
            MetricColumnItem(key="owner_name", label="Owner / Contact", type="string"),
            MetricColumnItem(key="area", label="Area", type="string"),
            MetricColumnItem(key="city", label="City", type="string"),
            MetricColumnItem(key="visit_type", label="Visit Type", type="string"),
            MetricColumnItem(key="address", label="Address", type="string"),
            MetricColumnItem(key="verified", label="Verified", type="status"),
            MetricColumnItem(key="pob_amount", label="POB Amount", type="currency", align="right"),
        ]

        visits = (
            query.options(selectinload(DcrVisit.chemist).joinedload(Chemist.area))
            .order_by(DcrVisit.dcr_date.desc(), DcrVisit.call_time.desc())
            .offset((ctx.page - 1) * ctx.page_size)
            .limit(ctx.page_size)
            .all()
        )

        rows = []
        for v in visits:
            ch = v.chemist
            area_name = ch.area.name if ch and getattr(ch, "area", None) else "-"
            rows.append({
                "id": str(v.id),
                "date": v.dcr_date.isoformat() if v.dcr_date else "-",
                "time": v.call_time.strftime("%H:%M") if v.call_time else "-",
                "chemist_name": ch.shop_name if ch else "Unknown Chemist",
                "owner_name": ch.contact_person if ch else "-",
                "area": area_name,
                "city": area_name,
                "visit_type": v.visit_type or "Regular",
                "address": ch.address if ch else "-",
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
