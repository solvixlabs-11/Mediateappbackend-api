"""Metric Handler: Stockist Visits (TABLE)."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import selectinload

from app.modules.customers.models import Stockist
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse
from app.modules.dcr.models import DcrVisit


class StockistVisitsMetric(BaseMetricHandler):
    key = "stockist_visits"
    title = "Stockist Visits"
    kind = "TABLE"
    color_group = "primary"

    def _get_base_query(self, ctx: MetricHandlerContext):
        return (
            ctx.db.query(DcrVisit)
            .filter(
                DcrVisit.user_id == ctx.employee.id,
                DcrVisit.customer_type == "STOCKIST",
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
            MetricColumnItem(key="stockist_name", label="Stockist Agency", type="string"),
            MetricColumnItem(key="contact_person", label="Contact Person", type="string"),
            MetricColumnItem(key="city", label="City", type="string"),
            MetricColumnItem(key="area", label="Area", type="string"),
            MetricColumnItem(key="visit_type", label="Visit Type", type="string"),
            MetricColumnItem(key="address", label="Address", type="string"),
            MetricColumnItem(key="verified", label="Verified", type="status"),
        ]

        visits = (
            query.options(selectinload(DcrVisit.stockist).joinedload(Stockist.area))
            .order_by(DcrVisit.dcr_date.desc(), DcrVisit.call_time.desc())
            .offset((ctx.page - 1) * ctx.page_size)
            .limit(ctx.page_size)
            .all()
        )

        rows = []
        for v in visits:
            st = v.stockist
            area_name = st.area.name if st and getattr(st, "area", None) else "-"
            rows.append({
                "id": str(v.id),
                "date": v.dcr_date.isoformat() if v.dcr_date else "-",
                "time": v.call_time.strftime("%H:%M") if v.call_time else "-",
                "stockist_name": st.agency_name if st else "Unknown Stockist",
                "contact_person": st.contact_person if st else "-",
                "city": area_name,
                "area": area_name,
                "visit_type": v.visit_type or "Regular",
                "address": st.address if st else "-",
                "verified": "VERIFIED" if v.is_geofence_verified else "UNVERIFIED",
            })

        return MetricDetailResponse(
            meta=self.build_meta(ctx, columns),
            rows=rows,
            total=total,
            page=ctx.page,
            page_size=ctx.page_size,
        )
