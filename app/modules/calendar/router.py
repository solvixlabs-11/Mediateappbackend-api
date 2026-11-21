"""Unified Calendar REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.calendar.schemas import CalendarMonthResponse
from app.modules.calendar.service import CalendarService
from app.modules.users.models import User

router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get(
    "/month",
    response_model=CalendarMonthResponse,
    summary="Get monthly calendar with per-day operational counts and events",
)
def get_month_calendar(
    employee_id: int | None = Query(
        default=None, description="Employee ID (defaults to authenticated user)"
    ),
    year: int | None = Query(default=None, description="Calendar year (defaults to current year)"),
    month: int | None = Query(
        default=None, ge=1, le=12, description="Calendar month (1-12, defaults to current month)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CalendarMonthResponse:
    """Fetch day-by-day counts (Doctor, Chemist, Stockist, New Customers, POB) and scheduled events."""
    service = CalendarService(db)
    return service.get_month_calendar(
        employee_id=employee_id,
        year=year,
        month=month,
        current_user=current_user,
    )
