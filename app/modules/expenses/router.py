"""Expense Claims REST API endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.expenses.schemas import (
    ExpenseCreateRequest,
    ExpenseResponse,
    MonthlyExpenseSummaryResponse,
)
from app.modules.expenses.service import ExpenseService
from app.modules.users.models import User

router = APIRouter(prefix="/expenses", tags=["Expenses"])


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
