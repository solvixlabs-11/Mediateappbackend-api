"""Tour Program & Tour Plan Cutoff Lock REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_permission
from app.modules.tours.schemas import (
    TourPlanLockCreateRequest,
    TourPlanLockResponse,
    TourPlanUnlockRequest,
    TourProgramCreateRequest,
    TourProgramResponse,
)
from app.modules.tours.service import TourService
from app.modules.users.models import User

router = APIRouter(tags=["Tour Programs"])


@router.post(
    "/tours",
    response_model=TourProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and submit a Tour Program (BR-09)",
)
def create_tour(
    payload: TourProgramCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TourProgramResponse:
    """Submit a new monthly/weekly tour plan for manager approval."""
    service = TourService(db)
    return service.create_tour(payload, current_user)


@router.get(
    "/tours",
    response_model=list[TourProgramResponse],
    summary="List Tour Programs scoped to role",
)
def list_tours(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TourProgramResponse]:
    """Fetch tour programs for rep or manager's team."""
    service = TourService(db)
    return service.list_tours(current_user)


@router.get(
    "/tours/{tour_id}",
    response_model=TourProgramResponse,
    summary="Get single Tour Program details",
)
def get_tour(
    tour_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TourProgramResponse:
    """Fetch tour by ID."""
    service = TourService(db)
    return service.get_tour(tour_id)


# --- Tour Plan Lock Endpoints ---


@router.get(
    "/tour-plan-locks",
    response_model=list[TourPlanLockResponse],
    summary="List active and historical tour plan locks",
)
def list_tour_plan_locks(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2020, le=2050),
    scope: str | None = Query(default=None, description="ALL, TERRITORY, EMPLOYEE, or ALL_SCOPES"),
    status: str | None = Query(default=None, description="LOCKED, UNLOCKED, or ALL"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TourPlanLockResponse]:
    """Fetch tour plan cutoff locks."""
    service = TourService(db)
    return service.list_locks(month=month, year=year, scope=scope, status=status)


@router.get(
    "/tour-plan-locks/history",
    response_model=list[TourPlanLockResponse],
    summary="Fetch audit history of tour plan locks",
)
def get_tour_plan_lock_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settings:read")),
) -> list[TourPlanLockResponse]:
    """Audit history log of all lock/unlock events."""
    service = TourService(db)
    return service.get_lock_history()


@router.post(
    "/tour-plan-locks",
    response_model=TourPlanLockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Establish a cutoff lock on tour plan submissions (Admin only)",
)
def create_tour_plan_lock(
    payload: TourPlanLockCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settings:write")),
) -> TourPlanLockResponse:
    """Establish cutoff deadline lock for a given month and scope."""
    service = TourService(db)
    return service.create_lock(payload, admin_user=current_user)


@router.post(
    "/tour-plan-locks/{lock_id}/unlock",
    response_model=TourPlanLockResponse,
    summary="Unlock tour plan submissions with audited reason (Admin only)",
)
def unlock_tour_plan_lock(
    lock_id: int,
    payload: TourPlanUnlockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settings:write")),
) -> TourPlanLockResponse:
    """Unlock an established tour plan lock."""
    service = TourService(db)
    return service.unlock_lock(lock_id, payload, admin_user=current_user)
