"""Masters REST HTTP endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.modules.masters.schemas import (
    AreaCreate,
    AreaResponse,
    AreaUpdate,
    CityCreate,
    CityResponse,
    CityUpdate,
    MasterBulkDropdownsResponse,
    MasterItemCreate,
    MasterItemResponse,
    MasterItemUpdate,
    StateCreate,
    StateResponse,
    StateUpdate,
)
from app.modules.masters.service import MasterService
from app.modules.users.models import User

router = APIRouter(prefix="/masters", tags=["Masters"])


@router.get(
    "/bulk-dropdowns",
    response_model=MasterBulkDropdownsResponse,
    summary="Get all common dropdowns for offline caching",
)
def get_bulk_dropdowns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MasterBulkDropdownsResponse:
    """Fetch bundled specializations, categories, and states for client cache."""
    service = MasterService(db)
    return service.get_bulk_dropdowns()


@router.get(
    "",
    response_model=list[MasterItemResponse],
    summary="List generic master items",
)
def list_master_items(
    type: str | None = Query(
        default=None, description="Item type: SPECIALIZATION, CUSTOMER_CATEGORY, VISIT_PRIORITY"
    ),
    active_only: bool = Query(default=True, description="Filter only active items"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MasterItemResponse]:
    """Fetch list of business master items."""
    service = MasterService(db)
    return service.list_items(item_type=type, active_only=active_only)


@router.post(
    "",
    response_model=MasterItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create master item (Admin)",
)
def create_master_item(
    payload: MasterItemCreate,
    type: str | None = Query(default=None, description="Optional fallback type query param"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> MasterItemResponse:
    """Create a new master item."""
    service = MasterService(db)
    return service.create_item(payload, fallback_type=type, user_id=current_user.id)


@router.put(
    "/{item_id}",
    response_model=MasterItemResponse,
    summary="Update master item (Admin)",
)
def update_master_item(
    item_id: int,
    payload: MasterItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> MasterItemResponse:
    """Update existing master item."""
    service = MasterService(db)
    return service.update_item(item_id, payload, user_id=current_user.id)


@router.delete(
    "/{item_id}",
    summary="Delete master item (Admin)",
)
def delete_master_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> dict[str, str]:
    """Soft-delete existing master item."""
    service = MasterService(db)
    return service.delete_item(item_id, user_id=current_user.id)


# States
@router.get(
    "/states",
    response_model=list[StateResponse],
    summary="List states",
)
def list_states(
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StateResponse]:
    """List states."""
    service = MasterService(db)
    return service.list_states(active_only=active_only)


@router.post(
    "/states",
    response_model=StateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create state (Admin)",
)
def create_state(
    payload: StateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> StateResponse:
    """Create a state."""
    service = MasterService(db)
    return service.create_state(payload, user_id=current_user.id)


@router.put(
    "/states/{state_id}",
    response_model=StateResponse,
    summary="Update state (Admin)",
)
def update_state(
    state_id: int,
    payload: StateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> StateResponse:
    """Update existing state."""
    service = MasterService(db)
    return service.update_state(state_id, payload, user_id=current_user.id)


@router.delete(
    "/states/{state_id}",
    summary="Delete state (Admin)",
)
def delete_state(
    state_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> dict[str, str]:
    """Delete a state."""
    service = MasterService(db)
    return service.delete_state(state_id, user_id=current_user.id)


# Cities
@router.get(
    "/cities",
    response_model=list[CityResponse],
    summary="List cities by state",
)
def list_cities(
    state_id: int | None = Query(default=None),
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CityResponse]:
    """List cities."""
    service = MasterService(db)
    return service.list_cities(state_id=state_id, active_only=active_only)


@router.post(
    "/cities",
    response_model=CityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create city (Admin)",
)
def create_city(
    payload: CityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> CityResponse:
    """Create a city."""
    service = MasterService(db)
    return service.create_city(payload, user_id=current_user.id)


@router.put(
    "/cities/{city_id}",
    response_model=CityResponse,
    summary="Update city (Admin)",
)
def update_city(
    city_id: int,
    payload: CityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> CityResponse:
    """Update existing city."""
    service = MasterService(db)
    return service.update_city(city_id, payload, user_id=current_user.id)


@router.delete(
    "/cities/{city_id}",
    summary="Delete city (Admin)",
)
def delete_city(
    city_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> dict[str, str]:
    """Delete a city."""
    service = MasterService(db)
    return service.delete_city(city_id, user_id=current_user.id)


# Areas
@router.get(
    "/areas",
    response_model=list[AreaResponse],
    summary="List areas by city",
)
def list_areas(
    city_id: int | None = Query(default=None),
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AreaResponse]:
    """List areas."""
    service = MasterService(db)
    return service.list_areas(city_id=city_id, active_only=active_only)


@router.post(
    "/areas",
    response_model=AreaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create area (Admin)",
)
def create_area(
    payload: AreaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> AreaResponse:
    """Create an area."""
    service = MasterService(db)
    return service.create_area(payload, user_id=current_user.id)


@router.put(
    "/areas/{area_id}",
    response_model=AreaResponse,
    summary="Update area (Admin)",
)
def update_area(
    area_id: int,
    payload: AreaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> AreaResponse:
    """Update existing area."""
    service = MasterService(db)
    return service.update_area(area_id, payload, user_id=current_user.id)


@router.delete(
    "/areas/{area_id}",
    summary="Delete area (Admin)",
)
def delete_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> dict[str, str]:
    """Delete an area."""
    service = MasterService(db)
    return service.delete_area(area_id, user_id=current_user.id)
