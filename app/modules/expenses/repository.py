"""Expense Claims database repository."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.expenses.models import Expense


class ExpenseRepository:
    """Repository handling expense entries and monthly KPI aggregations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, expense_id: int) -> Expense | None:
        return self.db.query(Expense).filter(Expense.id == expense_id).first()

    def get_by_client_uuid(self, client_uuid: str) -> Expense | None:
        return self.db.query(Expense).filter(Expense.client_uuid == client_uuid).first()

    def create(
        self,
        user_id: int,
        expense_date: date,
        expense_type: str,
        amount: float,
        description: str | None = None,
        receipt_file_id: int | None = None,
        client_uuid: str | None = None,
    ) -> Expense:
        exp = Expense(
            user_id=user_id,
            expense_date=expense_date,
            expense_type=expense_type,
            amount=amount,
            description=description,
            receipt_file_id=receipt_file_id,
            client_uuid=client_uuid,
            status="SUBMITTED",
        )
        self.db.add(exp)
        self.db.flush()
        return exp

    def list_expenses(
        self,
        user_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Expense]:
        query = self.db.query(Expense)
        if user_id:
            query = query.filter(Expense.user_id == user_id)
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        return query.order_by(Expense.expense_date.desc()).all()

    def get_monthly_summary(
        self,
        user_id: int,
        year: int,
        month: int,
    ) -> dict[str, float | int]:
        """Aggregate total claimed, approved, and pending amounts for the month."""
        query = (
            self.db.query(
                Expense.status,
                func.coalesce(func.sum(Expense.amount), 0.0),
                func.count(Expense.id),
            )
            .filter(
                Expense.user_id == user_id,
                func.extract("year", Expense.expense_date) == year,
                func.extract("month", Expense.expense_date) == month,
            )
            .group_by(Expense.status)
            .all()
        )

        total_claimed = 0.0
        total_approved = 0.0
        total_rejected = 0.0
        total_pending = 0.0
        total_count = 0

        for status_val, sum_val, count_val in query:
            amount = float(sum_val)
            total_claimed += amount
            total_count += count_val
            if status_val == "APPROVED":
                total_approved += amount
            elif status_val == "REJECTED":
                total_rejected += amount
            elif status_val == "SUBMITTED":
                total_pending += amount

        return {
            "year": year,
            "month": month,
            "total_claimed": total_claimed,
            "total_approved": total_approved,
            "total_rejected": total_rejected,
            "total_pending": total_pending,
            "claim_count": total_count,
        }
