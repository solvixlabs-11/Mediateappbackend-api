"""MR_Wise_Monthly_Expense_Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.expenses.models import Expense
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class ExpenseReport(BaseReport):
    key = "expense_report"
    title = "MR_Wise_Monthly_Expense_Report"
    group = "Plans & HR"
    description = "Expense per employee for a month."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="expense_type", label="Expense Type", type="string", align="center"),
            ReportColumn(key="expense_date", label="Date", type="date", align="center"),
            ReportColumn(key="amount", label="Amount Claimed (₹)", type="currency", align="right"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        q = select(Expense)
        if user_ids:
            q = q.where(Expense.user_id.in_(user_ids))
        claims = db.execute(q).scalars().all()
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}

        rows = []
        for c in claims:
            u = user_cache.get(c.user_id)
            rows.append({
                "employee": u.full_name if u else f"User #{c.user_id}",
                "expense_type": c.expense_type,
                "expense_date": c.expense_date.isoformat(),
                "amount": float(c.amount or 0.0),
                "status": c.status,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_claims": len(items),
            "total_claimed_amount": round(sum(float(i.get("amount", 0.0)) for i in items), 2),
        }

ReportEngineRegistry.register(ExpenseReport)
