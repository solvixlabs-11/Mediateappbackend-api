"""Group E: Stock and orders reports (Reports 18 to 19)."""

from __future__ import annotations

from typing import Any

from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn


class MrWiseSampleBalanceReport(BaseReport):
    """Report 18: MR Wise Sample Balance Report (P8 - Coming soon).

    Columns: MR, Item, Opening, Allocated, Distributed, Returned, Balance.
    """

    key = "mr_wise_sample_balance_report"
    title = "MR Wise Sample Balance Report"
    group = "Stock and Orders"
    description = "Field inventory ledger tracking physician sample allocation, distribution, and closing balances."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 18
    status = "P8"
    is_ready = False
    coming_soon_reason = "Needs Phase 8 data (sample inventory ledger, batch allocation, and returns)"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="item", label="Product / Sample Item", type="string"),
            ReportColumn(key="opening", label="Opening", type="number", align="right"),
            ReportColumn(key="allocated", label="Allocated", type="number", align="right"),
            ReportColumn(key="distributed", label="Distributed", type="number", align="right"),
            ReportColumn(key="returned", label="Returned", type="number", align="right"),
            ReportColumn(key="balance", label="Balance", type="number", align="right"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


class OrderRegisterReport(BaseReport):
    """Report 19: Order Register (P8 - Coming soon).

    Columns: Order no, Date, MR, Customer, Items count, Quantity, Status.
    """

    key = "order_register"
    title = "Order Register"
    group = "Stock and Orders"
    description = "Comprehensive order register for primary and secondary chemist orders booking."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 19
    status = "P8"
    is_ready = False
    coming_soon_reason = "Needs Phase 8 data (orders master, line items, and fulfillment workflow)"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="order_no", label="Order No", type="string", align="center"),
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="customer", label="Customer", type="string"),
            ReportColumn(key="items_count", label="Items Count", type="number", align="right"),
            ReportColumn(key="quantity", label="Total Qty", type="number", align="right"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


ReportRegistry.register(MrWiseSampleBalanceReport)
ReportRegistry.register(OrderRegisterReport)
