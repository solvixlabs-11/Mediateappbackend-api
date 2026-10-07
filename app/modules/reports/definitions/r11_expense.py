"""R11 - Expense Claims Report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.expenses.models import Expense
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.reports.utils import utc_to_ist_date


class ExpenseReport(BaseReport):
    """R11 Expense.

    Claims by date, type, amount, receipt, status, approver; totals.
    """

    key = "expense_report"
    title = "Expense Report"
    group = "HR and Expense"
    description = "Daily travel, food, and lodging allowance claims, receipts attachment audit, and manager approval sign-offs."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        status_picker=True,
        status_options=["All", "PENDING", "APPROVED", "REJECTED"],
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="type", label="Type", type="string"),
            ReportColumn(key="amount", label="Amount", type="currency", align="right"),
            ReportColumn(key="description", label="Description", type="string"),
            ReportColumn(key="receipt", label="Receipt", type="status", align="center"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
            ReportColumn(key="approver", label="Approver", type="string"),
            ReportColumn(key="approved_on", label="Approved On", type="date", align="center"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(Expense)
            .options(
                selectinload(Expense.user),
            )
            .order_by(Expense.expense_date.desc())
        )

        if user_ids is not None:
            stmt = stmt.where(Expense.user_id.in_(user_ids))
        if start_utc and end_utc:
            stmt = stmt.where(
                Expense.created_at >= start_utc,
                Expense.created_at <= end_utc,
            )
        if filters.status and filters.status.lower() != "all":
            stmt = stmt.where(Expense.status == filters.status.upper())

        records = db.scalars(stmt).all()
        results: list[dict[str, Any]] = []

        for exp in records:
            amt = round(float(exp.amount), 2)
            has_rec = "Yes" if exp.receipt_file_id is not None else "No"
            app_on = utc_to_ist_date(exp.updated_at) if exp.status == "APPROVED" else "-"

            results.append(
                {
                    "date": exp.expense_date.isoformat(),
                    "mr_name": exp.user.full_name if exp.user else f"MR #{exp.user_id}",
                    "type": exp.expense_type.replace("_", " ").title(),
                    "amount": amt,
                    "description": exp.description or "-",
                    "receipt": has_rec,
                    "status": exp.status.title(),
                    "approver": "Branch Manager" if exp.status == "APPROVED" else "-",
                    "approved_on": app_on,
                    "_raw_amount": amt,
                    "_raw_status": exp.status,
                }
            )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_claimed = round(sum(float(it.get("_raw_amount", 0.0)) for it in items), 2)
        total_approved = round(
            sum(
                float(it.get("_raw_amount", 0.0))
                for it in items
                if it.get("_raw_status") == "APPROVED"
            ),
            2,
        )
        total_pending = round(
            sum(
                float(it.get("_raw_amount", 0.0))
                for it in items
                if it.get("_raw_status") == "PENDING"
            ),
            2,
        )
        total_rejected = round(
            sum(
                float(it.get("_raw_amount", 0.0))
                for it in items
                if it.get("_raw_status") == "REJECTED"
            ),
            2,
        )

        return {
            "total_claimed": total_claimed,
            "total_approved": total_approved,
            "total_pending": total_pending,
            "total_rejected": total_rejected,
        }


ReportRegistry.register(ExpenseReport)
