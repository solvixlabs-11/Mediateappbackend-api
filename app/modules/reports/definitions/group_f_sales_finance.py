"""Group F: Sales and finance reports (Reports 20 to 25)."""

from __future__ import annotations

from typing import Any

from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn


class MrWiseChemistWiseSalesReport(BaseReport):
    """Report 20: MR Wise Chemist Wise Sales (SALES - Coming soon).

    Columns: MR, Chemist, Month, Quantity, Sales amount.
    """

    key = "mr_wise_chemist_wise_sales"
    title = "MR Wise Chemist Wise Sales"
    group = "Sales and Finance"
    description = "Chemist-level sales performance and liquidation tracking by representative."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 20
    status = "SALES"
    is_ready = False
    coming_soon_reason = "Needs new sales and finance data (requires invoice upload or secondary sales capture)"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="chemist", label="Chemist", type="string"),
            ReportColumn(key="month", label="Month", type="string", align="center"),
            ReportColumn(key="quantity", label="Quantity", type="number", align="right"),
            ReportColumn(key="sales_amount", label="Sales Amount", type="currency", align="right"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


class MrWiseStockistWiseSalesReport(BaseReport):
    """Report 21: MR Wise Stockist Wise Sales (SALES - Coming soon).

    Columns: MR, Stockist, Month, Quantity, Sales amount.
    """

    key = "mr_wise_stockist_wise_sales"
    title = "MR Wise Stockist Wise Sales"
    group = "Sales and Finance"
    description = "Stockist-wise primary billing, sales turnover, and supply fulfillment report."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 21
    status = "SALES"
    is_ready = False
    coming_soon_reason = "Needs new sales and finance data (requires distributor invoices or ERP integration)"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="stockist", label="Stockist Agency", type="string"),
            ReportColumn(key="month", label="Month", type="string", align="center"),
            ReportColumn(key="quantity", label="Quantity", type="number", align="right"),
            ReportColumn(key="sales_amount", label="Sales Amount", type="currency", align="right"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


class MrWiseMonthlyBusinessReport(BaseReport):
    """Report 22: MR Wise Monthly Business Report (SALES - Coming soon).

    Columns: MR, Month, Target, Sales achieved, Achievement %, Growth vs last month.
    """

    key = "mr_wise_monthly_business_report"
    title = "MR Wise Monthly Business Report"
    group = "Sales and Finance"
    description = "Executive commercial scorecard tracking sales targets, actual revenue achievements, and month-on-month growth."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 22
    status = "SALES"
    is_ready = False
    coming_soon_reason = "Needs new sales and finance data (requires commercial targets vs sales ledger)"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="month", label="Month", type="string", align="center"),
            ReportColumn(key="target", label="Target", type="currency", align="right"),
            ReportColumn(key="sales_achieved", label="Sales Achieved", type="currency", align="right"),
            ReportColumn(key="achievement_pct", label="Achievement %", type="percent", align="right"),
            ReportColumn(key="growth_pct", label="MoM Growth %", type="percent", align="right"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


class CollectionReport(BaseReport):
    """Report 23: Collection Report (SALES - Coming soon).

    Columns: Date, Customer, Receipt no, Mode, Amount, MR.
    """

    key = "collection_report"
    title = "Collection Report"
    group = "Sales and Finance"
    description = "Payment receipts and bank collections ledger logged against outstanding customer balances."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 23
    status = "SALES"
    is_ready = False
    coming_soon_reason = "Needs new sales and finance data (requires collection receipts data)"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="customer", label="Customer", type="string"),
            ReportColumn(key="receipt_no", label="Receipt No", type="string", align="center"),
            ReportColumn(key="mode", label="Payment Mode", type="string", align="center"),
            ReportColumn(key="amount", label="Amount", type="currency", align="right"),
            ReportColumn(key="mr_name", label="MR", type="string"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


class CreditNoteReport(BaseReport):
    """Report 24: Credit Note Report (SALES - Coming soon).

    Columns: Credit note no, Date, Customer, Reason, Amount, MR.
    """

    key = "credit_note_report"
    title = "Credit Note Report"
    group = "Sales and Finance"
    description = "Authorized credit notes issued for trade discounts, breakage, product returns, and rate adjustments."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 24
    status = "SALES"
    is_ready = False
    coming_soon_reason = "Needs new sales and finance data (requires credit notes ledger)"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="credit_note_no", label="Credit Note #", type="string", align="center"),
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="customer", label="Customer", type="string"),
            ReportColumn(key="reason", label="Reason", type="string"),
            ReportColumn(key="amount", label="Amount", type="currency", align="right"),
            ReportColumn(key="mr_name", label="MR", type="string"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


class OutstandingReport(BaseReport):
    """Report 25: Outstanding Report (SALES - Coming soon).

    Columns: Customer, Invoice no, Invoice date, Amount, Paid, Outstanding, Days overdue, MR.
    """

    key = "outstanding_report"
    title = "OutStanding Report"
    group = "Sales and Finance"
    description = "Receivables aging analysis tracking pending invoices, overdue days, and collection exposure."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 25
    status = "SALES"
    is_ready = False
    coming_soon_reason = "Needs new sales and finance data (requires invoice aging ledger)"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="customer", label="Customer", type="string"),
            ReportColumn(key="invoice_no", label="Invoice No", type="string", align="center"),
            ReportColumn(key="invoice_date", label="Invoice Date", type="date", align="center"),
            ReportColumn(key="amount", label="Invoice Amount", type="currency", align="right"),
            ReportColumn(key="paid", label="Amount Paid", type="currency", align="right"),
            ReportColumn(key="outstanding", label="Outstanding", type="currency", align="right"),
            ReportColumn(key="days_overdue", label="Days Overdue", type="number", align="right"),
            ReportColumn(key="mr_name", label="MR", type="string"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


ReportRegistry.register(MrWiseChemistWiseSalesReport)
ReportRegistry.register(MrWiseStockistWiseSalesReport)
ReportRegistry.register(MrWiseMonthlyBusinessReport)
ReportRegistry.register(CollectionReport)
ReportRegistry.register(CreditNoteReport)
ReportRegistry.register(OutstandingReport)
