"""Metric Handler: New Chemist Visits (TABLE)."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

from sqlalchemy.orm import selectinload

from app.modules.customers.models import Chemist
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse


class NewChemistVisitsMetric(BaseMetricHandler):
    key = "new_chemist_visits"
    title = "New Chemist Visits"
    kind = "TABLE"
    color_group = "primary"

    def _get_base_query(self, ctx: MetricHandlerContext):
        start_dt = datetime.combine(ctx.from_date, time.min)
        end_dt = datetime.combine(ctx.to_date, time.max)
        return (
            ctx.db.query(Chemist)
            .filter(
                Chemist.created_by == ctx.employee.id,
                Chemist.created_at >= start_dt,
                Chemist.created_at <= end_dt,
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
            MetricColumnItem(key="name", label="Chemist Name", type="string"),
            MetricColumnItem(key="owner", label="Owner / Contact", type="string"),
            MetricColumnItem(key="mobile", label="Mobile", type="string"),
            MetricColumnItem(key="city", label="City", type="string"),
            MetricColumnItem(key="area", label="Area", type="string"),
            MetricColumnItem(key="approval_status", label="Approval Status", type="status"),
            MetricColumnItem(key="address", label="Address", type="string"),
        ]

        chemists = (
            query.options(selectinload(Chemist.area))
            .order_by(Chemist.created_at.desc())
            .offset((ctx.page - 1) * ctx.page_size)
            .limit(ctx.page_size)
            .all()
        )

        rows = []
        for ch in chemists:
            approval = getattr(ch, "approval_status", "APPROVED") or "APPROVED"
            area_name = ch.area.name if ch.area else "-"
            city_name = ch.area.city.name if (ch.area and getattr(ch.area, "city", None)) else "-"
            rows.append({
                "id": str(ch.id),
                "date": ch.created_at.strftime("%Y-%m-%d") if ch.created_at else "-",
                "name": ch.shop_name,
                "owner": ch.contact_person or "-",
                "mobile": ch.phone or "-",
                "city": city_name,
                "area": area_name,
                "approval_status": approval,
                "address": ch.address or "-",
            })

        return MetricDetailResponse(
            meta=self.build_meta(ctx, columns),
            rows=rows,
            total=total,
            page=ctx.page,
            page_size=ctx.page_size,
        )
