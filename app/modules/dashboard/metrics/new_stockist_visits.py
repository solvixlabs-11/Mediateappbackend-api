"""Metric Handler: New Stockist Visits (TABLE)."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

from sqlalchemy.orm import selectinload

from app.modules.customers.models import Stockist
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse


class NewStockistVisitsMetric(BaseMetricHandler):
    key = "new_stockist_visits"
    title = "New Stockist Visits"
    kind = "TABLE"
    color_group = "primary"

    def _get_base_query(self, ctx: MetricHandlerContext):
        start_dt = datetime.combine(ctx.from_date, time.min)
        end_dt = datetime.combine(ctx.to_date, time.max)
        return (
            ctx.db.query(Stockist)
            .filter(
                Stockist.created_by == ctx.employee.id,
                Stockist.created_at >= start_dt,
                Stockist.created_at <= end_dt,
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
            MetricColumnItem(key="name", label="Agency Name", type="string"),
            MetricColumnItem(key="owner", label="Contact Person", type="string"),
            MetricColumnItem(key="mobile", label="Mobile", type="string"),
            MetricColumnItem(key="city", label="City", type="string"),
            MetricColumnItem(key="area", label="Area", type="string"),
            MetricColumnItem(key="approval_status", label="Approval Status", type="status"),
            MetricColumnItem(key="address", label="Address", type="string"),
        ]

        stockists = (
            query.options(selectinload(Stockist.area))
            .order_by(Stockist.created_at.desc())
            .offset((ctx.page - 1) * ctx.page_size)
            .limit(ctx.page_size)
            .all()
        )

        rows = []
        for s in stockists:
            approval = getattr(s, "approval_status", "APPROVED") or "APPROVED"
            area_name = s.area.name if s.area else "-"
            city_name = s.area.city.name if (s.area and getattr(s.area, "city", None)) else "-"
            rows.append({
                "id": str(s.id),
                "date": s.created_at.strftime("%Y-%m-%d") if s.created_at else "-",
                "name": s.agency_name,
                "owner": s.contact_person or "-",
                "mobile": s.phone or "-",
                "city": city_name,
                "area": area_name,
                "approval_status": approval,
                "address": s.address or "-",
            })

        return MetricDetailResponse(
            meta=self.build_meta(ctx, columns),
            rows=rows,
            total=total,
            page=ctx.page,
            page_size=ctx.page_size,
        )
