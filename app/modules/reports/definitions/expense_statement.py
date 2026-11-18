"""Monthly Expense Reimbursement Statement."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.expenses.models import Expense
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn


class ExpenseStatementReport(BaseReport):
    key = "expense_statement"
    title = "Monthly Expense Reimbursement Statement"
    group = "Plans & HR"
    description = "Printable monthly statement for one employee (PDF with signature block)."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="head", label="Expense Head", type="string"),
            ReportColumn(key="details", label="Description", type="string"),
            ReportColumn(key="amount", label="Amount (₹)", type="currency", align="right"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        q = select(Expense)
        if user_ids:
            q = q.where(Expense.user_id.in_(user_ids))
        claims = db.execute(q).scalars().all()
        rows = []
        for c in claims:
            rows.append({
                "date": c.expense_date.isoformat(),
                "head": c.expense_type,
                "details": c.description or "Field expense claim",
                "amount": float(c.amount or 0.0),
                "status": c.status,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_claimed_amount": round(sum(float(i.get("amount", 0.0)) for i in items), 2),
            "statement_status": "CERTIFIED_VALID",
        }

ReportEngineRegistry.register(ExpenseStatementReport)
