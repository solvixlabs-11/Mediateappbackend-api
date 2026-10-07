"""Expense Claims business logic service."""

from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.approvals.repository import ApprovalRepository
from app.modules.expenses.models import Expense
from app.modules.expenses.repository import ExpenseRepository
from app.modules.expenses.schemas import (
    ExpenseCreateRequest,
    ExpenseResponse,
    MonthlyExpenseSummaryResponse,
)
from app.modules.users.models import User


class ExpenseService:
    """Service handling daily field expense claims and approval creation."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExpenseRepository(db)
        self.approval_repo = ApprovalRepository(db)

    def _to_response(self, exp: Expense) -> ExpenseResponse:
        return ExpenseResponse(
            id=exp.id,
            user_id=exp.user_id,
            user_name=exp.user.full_name if exp.user else None,
            expense_date=exp.expense_date,
            expense_type=exp.expense_type,
            amount=exp.amount,
            description=exp.description,
            receipt_file_id=exp.receipt_file_id,
            status=exp.status,
            approval_request_id=exp.approval_request_id,
            rejection_reason=exp.rejection_reason,
            created_at=exp.created_at,
            updated_at=exp.updated_at,
        )

    def create_expense(self, payload: ExpenseCreateRequest, user: User) -> ExpenseResponse:
        """Create and submit an expense claim with idempotency support (BR-12)."""
        # Idempotency check with client_uuid
        if payload.client_uuid:
            existing = self.repo.get_by_client_uuid(payload.client_uuid)
            if existing:
                return self._to_response(existing)

        if payload.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Expense amount must be greater than zero.",
            )

        exp = self.repo.create(
            user_id=user.id,
            expense_date=payload.expense_date,
            expense_type=payload.expense_type,
            amount=payload.amount,
            description=payload.description,
            receipt_file_id=payload.receipt_file_id,
            client_uuid=payload.client_uuid,
        )

        # Dispatch approval request into the manager's inbox
        approval_req = self.approval_repo.create_request(
            entity_type="EXPENSE",
            entity_id=exp.id,
            requester_id=user.id,
            title=f"Expense: ₹{exp.amount:,.2f} - {exp.expense_type.replace('_', ' ')}",
            details=f"Date: {exp.expense_date}. Description: {exp.description or 'N/A'}.",
        )
        exp.approval_request_id = approval_req.id

        self.db.commit()
        self.db.refresh(exp)
        return self._to_response(exp)

    def list_expenses(
        self,
        current_user: User,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ExpenseResponse]:
        """List expenses scoped to role."""
        role_code = current_user.role.code if current_user.role else "MR"
        user_id = None if role_code in ("ADMIN", "MANAGER") else current_user.id
        expenses = self.repo.list_expenses(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        return [self._to_response(e) for e in expenses]

    def get_monthly_summary(
        self,
        current_user: User,
        year: int | None = None,
        month: int | None = None,
    ) -> MonthlyExpenseSummaryResponse:
        """Fetch monthly expense total and claim breakdown."""
        today = date.today()
        target_year = year or today.year
        target_month = month or today.month

        summary_dict = self.repo.get_monthly_summary(
            user_id=current_user.id,
            year=target_year,
            month=target_month,
        )
        return MonthlyExpenseSummaryResponse(**summary_dict)  # type: ignore[arg-type]
