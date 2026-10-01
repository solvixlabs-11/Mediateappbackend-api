"""Leave Management REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.leaves.schemas import (
    LeaveApplyRequest,
    LeaveBalanceResponse,
    LeaveResponse,
)
from app.modules.leaves.service import LeaveService
from app.modules.users.models import User

router = APIRouter(prefix="/leaves", tags=["Leaves"])


@router.get(
    "/balances",
    response_model=LeaveBalanceResponse,
    summary="Get current leave balances for rep",
)
def get_leave_balances(
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaveBalanceResponse:
    """Fetch remaining Casual, Sick, and Earned leave balances."""
    service = LeaveService(db)
    return service.get_balances(current_user, year=year)


@router.post(
    "",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for leave (BR-09, BR-10)",
)
def apply_leave(
    payload: LeaveApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaveResponse:
    """Submit a leave application for manager approval."""
    service = LeaveService(db)
    return service.apply_leave(payload, current_user)


@router.get(
    "",
    response_model=list[LeaveResponse],
    summary="List leave applications scoped to role",
)
def list_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LeaveResponse]:
    """Fetch leave requests history."""
    service = LeaveService(db)
    return service.list_leaves(current_user)


@router.post(
    "/{leave_id}/cancel",
    response_model=LeaveResponse,
    summary="Cancel a leave request and restore balance (BR-10)",
)
def cancel_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaveResponse:
    """Cancel leave request; restores deducted balance if it was approved."""
    service = LeaveService(db)
    return service.cancel_leave(leave_id, current_user)
