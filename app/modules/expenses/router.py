"""Expense Claims REST API endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.expenses.schemas import (
    ExpenseCreateRequest,
    ExpenseLimitBulkUpsertRequest,
    ExpenseLimitMatrixResponse,
    ExpenseLimitResponse,
    ExpensePayoutRequest,
    ExpenseResponse,
    MonthlyExpenseSummaryResponse,
)
from app.modules.expenses.service import ExpenseService
from app.modules.users.models import User

router = APIRouter(prefix="/expenses", tags=["Expenses"])
limits_router = APIRouter(prefix="/expense-limits", tags=["Expense Limits"])


def _check_expense_limits_write(current_user: User) -> None:
    if not current_user.role or current_user.role.code not in ["ADMIN", "ERP ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Modifying expense limits is restricted to administrators.",
        )


@limits_router.get(
    "",
    response_model=list[ExpenseLimitResponse],
    summary="List expense limits with optional filters",
)
def list_expense_limits(
    designation_id: int | None = Query(default=None),
    expense_type_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExpenseLimitResponse]:
    """Fetch designation-wise daily and monthly limits."""
    service = ExpenseService(db)
    return service.list_limits(designation_id=designation_id, expense_type_id=expense_type_id)


@limits_router.get(
    "/matrix",
    response_model=ExpenseLimitMatrixResponse,
    summary="Get full expense limits matrix across all designations",
)
def get_expense_limits_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseLimitMatrixResponse:
    """Fetch matrix grid of designations x expense types."""
    service = ExpenseService(db)
    return service.get_limits_matrix()


@limits_router.put(
    "/bulk",
    response_model=list[ExpenseLimitResponse],
    summary="Bulk upsert expense limits matrix",
)
def bulk_upsert_expense_limits(
    payload: ExpenseLimitBulkUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExpenseLimitResponse]:
    """Upsert expense limits matrix."""
    _check_expense_limits_write(current_user)
    service = ExpenseService(db)
    return service.bulk_upsert_limits(payload, current_user)


@limits_router.post(
    "/{limit_id}/confirm",
    response_model=ExpenseLimitResponse,
    summary="Confirm provisional expense limit",
)
def confirm_expense_limit(
    limit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseLimitResponse:
    """Acknowledge provisional limit as confirmed."""
    _check_expense_limits_write(current_user)
    service = ExpenseService(db)
    return service.confirm_limit(limit_id, current_user)



@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a field expense claim (DA/TA/Lodging)",
)
def create_expense(
    payload: ExpenseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Submit a daily expense claim for manager approval."""
    service = ExpenseService(db)
    return service.create_expense(payload, current_user)


@router.get(
    "",
    response_model=list[ExpenseResponse],
    summary="List expense claims scoped to user role",
)
def list_expenses(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExpenseResponse]:
    """Fetch expense claims history."""
    service = ExpenseService(db)
    return service.list_expenses(current_user, start_date=start_date, end_date=end_date)


@router.get(
    "/summary",
    response_model=MonthlyExpenseSummaryResponse,
    summary="Get monthly expense claim summary",
)
def get_monthly_summary(
    year: int | None = Query(default=None),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonthlyExpenseSummaryResponse:
    """Fetch monthly claimed vs approved totals."""
    service = ExpenseService(db)
    return service.get_monthly_summary(current_user, year=year, month=month)


def _check_expense_payout_permission(current_user: User) -> None:
    if not current_user.role or current_user.role.code not in ["ADMIN", "ERP ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Processing reimbursement payouts is restricted to administrators.",
        )


@router.get(
    "/payout-modes",
    response_model=list[str],
    summary="Get supported reimbursement payout modes",
)
def get_payout_modes(
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """Return available payment modes for reimbursement settlement."""
    return ["NEFT", "RTGS", "UPI", "CHEQUE", "CASH"]


@router.post(
    "/{expense_id}/payout",
    response_model=ExpenseResponse,
    summary="Process reimbursement payout for approved claim",
)
def process_payout(
    expense_id: int,
    payload: ExpensePayoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseResponse:
    """Settle an approved expense claim and mark as PAID with UTR reference."""
    _check_expense_payout_permission(current_user)
    service = ExpenseService(db)
    return service.process_payout(expense_id, payload, current_user)
