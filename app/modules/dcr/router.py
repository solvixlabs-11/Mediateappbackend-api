"""DCR REST API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.dcr.schemas import (
    DcrDailySummary,
    DcrVisitCreate,
    DcrVisitResponse,
    FollowUpCreate,
    FollowUpResponse,
    PlannedVisitCreate,
    PlannedVisitResponse,
)
from app.modules.dcr.service import DcrService
from app.modules.users.models import User

router = APIRouter(prefix="/dcr", tags=["Daily Call Report (DCR)"])


# 1. VISITS (Feature 7)
@router.post(
    "/visits",
    response_model=DcrVisitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit DCR call with geofence verification",
)
def submit_dcr_visit(
    payload: DcrVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DcrVisitResponse:
    """Submit doctor, chemist, hospital, or stockist call."""
    service = DcrService(db)
    return service.submit_dcr_visit(payload, current_user)


@router.get(
    "/visits",
    response_model=list[DcrVisitResponse],
    summary="List DCR visits for current user",
)
def list_dcr_visits(
    dcr_date: date | None = Query(default=None),
    customer_type: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DcrVisitResponse]:
    """Fetch user's DCR calls."""
    service = DcrService(db)
    return service.list_dcr_visits(
        current_user=current_user,
        dcr_date=dcr_date,
        customer_type=customer_type,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/visits/{visit_id}",
    response_model=DcrVisitResponse,
    summary="Get DCR visit details by ID",
)
def get_dcr_visit(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DcrVisitResponse:
    """Fetch full DCR record with post-call analysis and products."""
    service = DcrService(db)
    return service.get_dcr_visit_by_id(visit_id, current_user)


@router.get(
    "/summary",
    response_model=DcrDailySummary,
    summary="Get daily DCR metrics and call counts",
)
def get_daily_summary(
    dcr_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DcrDailySummary:
    """Get metrics for today or selected date."""
    service = DcrService(db)
    return service.get_daily_summary(current_user, dcr_date)


# 2. PRE-CALL PLANNING (Feature 8)
@router.post(
    "/plans",
    response_model=PlannedVisitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create planned customer visit",
)
def create_planned_visit(
    payload: PlannedVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlannedVisitResponse:
    """Add a customer to today or future plan."""
    service = DcrService(db)
    return service.create_planned_visit(payload, current_user)


@router.get(
    "/plans",
    response_model=list[PlannedVisitResponse],
    summary="List planned visits",
)
def list_planned_visits(
    plan_date: date | None = Query(default=None),
    status: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlannedVisitResponse]:
    """Fetch user's planned calls."""
    service = DcrService(db)
    return service.list_planned_visits(
        current_user=current_user,
        plan_date=plan_date,
        status=status,
        skip=skip,
        limit=limit,
    )


# 3. FOLLOW-UPS (Feature 23)
@router.post(
    "/follow-ups",
    response_model=FollowUpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer follow-up",
)
def create_follow_up(
    payload: FollowUpCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpResponse:
    """Create actionable follow-up reminder."""
    service = DcrService(db)
    return service.create_follow_up(payload, current_user)


@router.get(
    "/follow-ups",
    response_model=list[FollowUpResponse],
    summary="List customer follow-ups",
)
def list_follow_ups(
    status: str | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FollowUpResponse]:
    """Fetch pending or overdue follow-ups."""
    service = DcrService(db)
    return service.list_follow_ups(
        current_user=current_user,
        status=status,
        overdue_only=overdue_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/follow-ups/{follow_up_id}/complete",
    response_model=FollowUpResponse,
    summary="Mark follow-up as completed",
)
def complete_follow_up(
    follow_up_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpResponse:
    """Close completed follow-up."""
    service = DcrService(db)
    return service.complete_follow_up(follow_up_id, current_user)
