"""Territories REST HTTP endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.modules.territories.schemas import (
    AssignTerritoryRequest,
    TerritoryAssignmentResponse,
    TerritoryCreate,
    TerritoryResponse,
    TerritoryUpdate,
)
from app.modules.territories.service import TerritoryService
from app.modules.users.models import User

router = APIRouter(prefix="/territories", tags=["Territories"])


@router.get(
    "/my-territories",
    response_model=list[TerritoryResponse],
    summary="Get logged-in user's assigned territories",
)
def get_my_territories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TerritoryResponse]:
    """Fetch active territories assigned to current MR / Manager."""
    service = TerritoryService(db)
    return service.get_my_territories(current_user)


@router.get(
    "",
    response_model=list[TerritoryResponse],
    summary="List all territories",
)
def list_territories(
    search: str | None = Query(default=None),
    state_id: int | None = Query(default=None),
    active_only: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TerritoryResponse]:
    """List territories with search and state filter."""
    service = TerritoryService(db)
    return service.list_territories(
        search=search,
        state_id=state_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=TerritoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create territory (Admin)",
)
def create_territory(
    payload: TerritoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> TerritoryResponse:
    """Create a new territory and assign areas."""
    service = TerritoryService(db)
    return service.create_territory(payload, current_user)


@router.get(
    "/{territory_id}",
    response_model=TerritoryResponse,
    summary="Get territory details by ID",
)
def get_territory(
    territory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TerritoryResponse:
    """Get territory by ID."""
    service = TerritoryService(db)
    return service.get_territory_by_id(territory_id)


@router.put(
    "/{territory_id}",
    response_model=TerritoryResponse,
    summary="Update territory (Admin)",
)
def update_territory(
    territory_id: int,
    payload: TerritoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> TerritoryResponse:
    """Update territory metadata and areas."""
    service = TerritoryService(db)
    return service.update_territory(territory_id, payload, current_user)


@router.post(
    "/{territory_id}/assign",
    response_model=TerritoryAssignmentResponse,
    summary="Assign user to territory",
)
def assign_user_to_territory(
    territory_id: int,
    payload: AssignTerritoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:manage_roles")),
) -> TerritoryAssignmentResponse:
    """Assign an MR or Manager to a territory."""
    service = TerritoryService(db)
    return service.assign_user(territory_id, payload, current_user)


@router.delete(
    "/{territory_id}/assign/{user_id}",
    summary="Unassign user from territory",
)
def unassign_user_from_territory(
    territory_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:manage_roles")),
) -> dict[str, str]:
    """Remove user from territory."""
    service = TerritoryService(db)
    return service.unassign_user(territory_id, user_id, current_user)
