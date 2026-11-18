"""Metric Handler: Total POB (TABLE - COMING_SOON)."""

from __future__ import annotations

from typing import Any

from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse


class TotalPobMetric(BaseMetricHandler):
    key = "total_pob"
    title = "Total POB"
    kind = "TABLE"
    color_group = "danger"
    status = "COMING_SOON"
    unavailable_reason = "Order booking and chemist POB billing integration will be activated in Phase 8"
    can_export = False

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        # Contract: Never invent numbers for unavailable metrics
        return None, "-"

    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        columns = [
            MetricColumnItem(key="order_no", label="Order No", type="string"),
            MetricColumnItem(key="customer_name", label="Customer Name", type="string"),
            MetricColumnItem(key="customer_type", label="Type", type="string"),
            MetricColumnItem(key="date", label="Order Date", type="date"),
            MetricColumnItem(key="quantity", label="Quantity", type="number", align="right"),
            MetricColumnItem(key="value", label="Order Value", type="currency", align="right"),
        ]

        return MetricDetailResponse(
            meta=self.build_meta(ctx, columns),
            rows=[],
            total=0,
            page=ctx.page,
            page_size=ctx.page_size,
        )
