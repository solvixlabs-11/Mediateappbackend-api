"""Master data business service."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.masters.repository import MasterRepository
from app.modules.masters.schemas import (
    AreaCreate,
    AreaResponse,
    CityCreate,
    CityResponse,
    MasterBulkDropdownsResponse,
    MasterItemCreate,
    MasterItemResponse,
    MasterItemUpdate,
    StateCreate,
    StateResponse,
)


class MasterService:
    """Service handling business logic for master data."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MasterRepository(db)

    def list_items(
        self, item_type: str | None = None, active_only: bool = True
    ) -> list[MasterItemResponse]:
        """Fetch master items optionally filtered by type."""
        items = self.repo.list_items(item_type=item_type, active_only=active_only)
        return [MasterItemResponse.model_validate(i) for i in items]

    def create_item(
        self, payload: MasterItemCreate, user_id: int | None = None
    ) -> MasterItemResponse:
        """Create a new master item with unique code check."""
        existing = self.repo.get_item_by_type_code(payload.type, payload.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Master item with type '{payload.type}' and code "
                    f"'{payload.code}' already exists"
                ),
            )
        item = self.repo.create_item(
            item_type=payload.type,
            code=payload.code,
            name=payload.name,
            description=payload.description,
            sort_order=payload.sort_order,
            created_by_user_id=user_id,
        )
        self.db.commit()
        self.db.refresh(item)
        return MasterItemResponse.model_validate(item)

    def update_item(
        self, item_id: int, payload: MasterItemUpdate, user_id: int | None = None
    ) -> MasterItemResponse:
        """Update existing master item."""
        item = self.repo.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Master item with ID {item_id} not found",
            )
        if payload.name is not None:
            item.name = payload.name.strip()
        if payload.description is not None:
            item.description = payload.description.strip()
        if payload.sort_order is not None:
            item.sort_order = payload.sort_order
        if payload.is_active is not None:
            item.is_active = payload.is_active

        item.updated_by = user_id
        self.db.commit()
        self.db.refresh(item)
        return MasterItemResponse.model_validate(item)

    def list_states(self, active_only: bool = True) -> list[StateResponse]:
        """Fetch all states."""
        states = self.repo.list_states(active_only=active_only)
        return [StateResponse.model_validate(s) for s in states]

    def create_state(self, payload: StateCreate, user_id: int | None = None) -> StateResponse:
        """Create a new State."""
        existing = self.repo.get_state_by_code(payload.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"State with code '{payload.code}' already exists",
            )
        state = self.repo.create_state(
            name=payload.name,
            code=payload.code,
            created_by_user_id=user_id,
        )
        self.db.commit()
        self.db.refresh(state)
        return StateResponse.model_validate(state)

    def list_cities(
        self, state_id: int | None = None, active_only: bool = True
    ) -> list[CityResponse]:
        """Fetch cities optionally filtered by state."""
        cities = self.repo.list_cities(state_id=state_id, active_only=active_only)
        return [CityResponse.model_validate(c) for c in cities]

    def create_city(self, payload: CityCreate, user_id: int | None = None) -> CityResponse:
        """Create a new City under a State."""
        state = self.repo.get_state_by_id(payload.state_id)
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"State with ID {payload.state_id} not found",
            )
        city = self.repo.create_city(
            state_id=payload.state_id,
            name=payload.name,
            code=payload.code,
            created_by_user_id=user_id,
        )
        self.db.commit()
        self.db.refresh(city)
        return CityResponse.model_validate(city)

    def list_areas(
        self, city_id: int | None = None, active_only: bool = True
    ) -> list[AreaResponse]:
        """Fetch areas optionally filtered by city."""
        areas = self.repo.list_areas(city_id=city_id, active_only=active_only)
        return [AreaResponse.model_validate(a) for a in areas]

    def create_area(self, payload: AreaCreate, user_id: int | None = None) -> AreaResponse:
        """Create a new Area under a City."""
        city = self.repo.get_city_by_id(payload.city_id)
        if not city:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City with ID {payload.city_id} not found",
            )
        area = self.repo.create_area(
            city_id=payload.city_id,
            name=payload.name,
            pincode=payload.pincode,
            created_by_user_id=user_id,
        )
        self.db.commit()
        self.db.refresh(area)
        return AreaResponse.model_validate(area)

    def get_bulk_dropdowns(self) -> MasterBulkDropdownsResponse:
        """Fetch common masters bundle in a single call for client offline caching."""
        specs = self.list_items(item_type="SPECIALIZATION", active_only=True)
        categories = self.list_items(item_type="CUSTOMER_CATEGORY", active_only=True)
        priorities = self.list_items(item_type="VISIT_PRIORITY", active_only=True)
        states = self.list_states(active_only=True)

        return MasterBulkDropdownsResponse(
            specializations=specs,
            categories=categories,
            priorities=priorities,
            states=states,
        )
