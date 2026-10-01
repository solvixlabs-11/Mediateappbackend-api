"""Attendance REST API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.attendance.schemas import (
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    AttendanceResponse,
)
from app.modules.attendance.service import AttendanceService
from app.modules.users.models import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get(
    "/today",
    response_model=AttendanceResponse | None,
    summary="Get today's attendance status for logged-in user",
)
def get_today_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttendanceResponse | None:
    """Check if MR has checked in or checked out today."""
    service = AttendanceService(db)
    return service.get_today_attendance(current_user)


@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record daily morning check-in",
)
def check_in(
    payload: AttendanceCheckInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttendanceResponse:
    """Record user check-in with GPS coordinates."""
    service = AttendanceService(db)
    return service.check_in(payload, current_user)


@router.post(
    "/check-out",
    response_model=AttendanceResponse,
    summary="Record daily evening check-out",
)
def check_out(
    payload: AttendanceCheckOutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttendanceResponse:
    """Record user check-out."""
    service = AttendanceService(db)
    return service.check_out(payload, current_user)


@router.get(
    "/history",
    response_model=list[AttendanceResponse],
    summary="Get user attendance history",
)
def get_attendance_history(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=31, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AttendanceResponse]:
    """Fetch attendance history for date range."""
    service = AttendanceService(db)
    return service.list_history(
        user=current_user,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
