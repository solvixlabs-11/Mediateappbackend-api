"""Master data business service."""

import re
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.masters.models import MasterItem
from app.modules.masters.repository import MasterRepository
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
        if not items and item_type:
            from app.modules.masters.seed import seed_masters

            try:
                seed_masters(self.db)
                items = self.repo.list_items(item_type=item_type, active_only=active_only)
            except Exception:
                pass
        return [MasterItemResponse.model_validate(i) for i in items]

    def create_item(
        self,
        payload: MasterItemCreate,
        fallback_type: str | None = None,
        user_id: int | None = None,
    ) -> MasterItemResponse:
        """Create a new master item with unique code check and auto-generation."""
        item_type = (payload.type or fallback_type or "GENERAL").upper().strip()
        code = (
            payload.code
            or re.sub(r"[^A-Za-z0-9]+", "_", payload.name.strip()).upper()
        )[:50]

        existing = (
            self.db.query(MasterItem)
            .filter(MasterItem.type == item_type, MasterItem.code == code)
            .first()
        )
        if existing:
            if existing.is_deleted:
                existing.is_deleted = False
                existing.is_active = True
                existing.name = payload.name.strip()
                existing.description = payload.description.strip() if payload.description else None
                existing.sort_order = payload.sort_order
                existing.updated_by = user_id
                self.db.commit()
                self.db.refresh(existing)
                return MasterItemResponse.model_validate(existing)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Master item '{payload.name}' ({code}) already exists in {item_type}",
            )

        item = self.repo.create_item(
            item_type=item_type,
            code=code,
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

    def delete_item(self, item_id: int, user_id: int | None = None) -> dict[str, str]:
        """Soft-delete a master item."""
        item = self.repo.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Master item with ID {item_id} not found",
            )
        self.repo.delete_item(item_id, user_id=user_id)
        self.db.commit()
        return {"status": "success", "message": f"Item {item_id} deleted successfully"}

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

    def update_state(
        self, state_id: int, payload: StateUpdate, user_id: int | None = None
    ) -> StateResponse:
        """Update existing State."""
        state = self.repo.update_state(
            state_id=state_id,
            name=payload.name,
            code=payload.code,
            is_active=payload.is_active,
            user_id=user_id,
        )
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"State with ID {state_id} not found",
            )
        self.db.commit()
        self.db.refresh(state)
        return StateResponse.model_validate(state)

    def delete_state(self, state_id: int, user_id: int | None = None) -> dict[str, str]:
        """Delete / soft-delete a state with relational check."""
        cities = self.repo.list_cities(state_id=state_id, active_only=True)
        if cities:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete state: {len(cities)} active cities are assigned to it.",
            )
        success = self.repo.delete_state(state_id, user_id=user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"State with ID {state_id} not found",
            )
        self.db.commit()
        return {"status": "success", "message": f"State {state_id} deleted successfully"}

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

    def update_city(
        self, city_id: int, payload: CityUpdate, user_id: int | None = None
    ) -> CityResponse:
        """Update existing City."""
        city = self.repo.update_city(
            city_id=city_id,
            name=payload.name,
            code=payload.code,
            state_id=payload.state_id,
            is_active=payload.is_active,
            user_id=user_id,
        )
        if not city:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City with ID {city_id} not found",
            )
        self.db.commit()
        self.db.refresh(city)
        return CityResponse.model_validate(city)

    def delete_city(self, city_id: int, user_id: int | None = None) -> dict[str, str]:
        """Delete / soft-delete a city with relational check."""
        areas = self.repo.list_areas(city_id=city_id, active_only=True)
        if areas:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete city: {len(areas)} active areas are assigned to it.",
            )
        success = self.repo.delete_city(city_id, user_id=user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City with ID {city_id} not found",
            )
        self.db.commit()
        return {"status": "success", "message": f"City {city_id} deleted successfully"}

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

    def update_area(
        self, area_id: int, payload: AreaUpdate, user_id: int | None = None
    ) -> AreaResponse:
        """Update existing Area."""
        area = self.repo.update_area(
            area_id=area_id,
            name=payload.name,
            pincode=payload.pincode,
            city_id=payload.city_id,
            is_active=payload.is_active,
            user_id=user_id,
        )
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Area with ID {area_id} not found",
            )
        self.db.commit()
        self.db.refresh(area)
        return AreaResponse.model_validate(area)

    def delete_area(self, area_id: int, user_id: int | None = None) -> dict[str, str]:
        """Delete / soft-delete an area."""
        success = self.repo.delete_area(area_id, user_id=user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Area with ID {area_id} not found",
            )
        self.db.commit()
        return {"status": "success", "message": f"Area {area_id} deleted successfully"}

    def get_bulk_dropdowns(self) -> MasterBulkDropdownsResponse:
        """Fetch common masters bundle in a single call for client offline caching."""
        specs = self.list_items(item_type="SPECIALIZATION", active_only=True)
        categories = self.list_items(item_type="CUSTOMER_CATEGORY", active_only=True)
        priorities = self.list_items(item_type="VISIT_PRIORITY", active_only=True)
        states = self.list_states(active_only=True)
        qualifications = self.list_items(item_type="QUALIFICATION", active_only=True)
        doctor_types = self.list_items(item_type="DOCTOR_TYPE", active_only=True)
        store_types = self.list_items(item_type="STORE_TYPE", active_only=True)
        distributor_types = self.list_items(item_type="DISTRIBUTOR_TYPE", active_only=True)
        credit_terms = self.list_items(item_type="CREDIT_TERMS", active_only=True)
        expense_types = self.list_items(item_type="EXPENSE_TYPE", active_only=True)
        zones = self.list_items(item_type="ZONE", active_only=True)
        city_tiers = self.list_items(item_type="CITY_TIER", active_only=True)
        hospital_types = self.list_items(item_type="HOSPITAL_TYPE", active_only=True)
        divisions = self.list_items(item_type="DIVISION", active_only=True)
        designations = self.list_items(item_type="DESIGNATION", active_only=True)
        customer_types = self.list_items(item_type="CUSTOMER_TYPE", active_only=True)
        approval_statuses = self.list_items(item_type="APPROVAL_STATUS", active_only=True)

        return MasterBulkDropdownsResponse(
            specializations=specs,
            categories=categories,
            priorities=priorities,
            states=states,
            qualifications=qualifications,
            doctor_types=doctor_types,
            store_types=store_types,
            distributor_types=distributor_types,
            credit_terms=credit_terms,
            expense_types=expense_types,
            zones=zones,
            city_tiers=city_tiers,
            hospital_types=hospital_types,
            divisions=divisions,
            designations=designations,
            customer_types=customer_types,
            approval_statuses=approval_statuses,
        )
