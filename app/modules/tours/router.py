"""Tour Program REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.tours.schemas import TourProgramCreateRequest, TourProgramResponse
from app.modules.tours.service import TourService
from app.modules.users.models import User

router = APIRouter(prefix="/tours", tags=["Tour Programs"])


@router.post(
    "",
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
    "",
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
    "/{tour_id}",
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
