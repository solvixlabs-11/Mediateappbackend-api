"""Master data database repository."""

from sqlalchemy.orm import Session

from app.modules.masters.models import Area, City, MasterItem, State


class MasterRepository:
    """Repository handling database operations for Master items, States, Cities, Areas."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # Master Items
    def list_items(
        self, item_type: str | None = None, active_only: bool = True
    ) -> list[MasterItem]:
        """List master items with optional type and active status filters."""
        query = self.db.query(MasterItem).filter(MasterItem.is_deleted == False)  # noqa: E712
        if item_type:
            query = query.filter(MasterItem.type == item_type.upper())
        if active_only:
            query = query.filter(MasterItem.is_active == True)  # noqa: E712
        return query.order_by(MasterItem.sort_order.asc(), MasterItem.name.asc()).all()

    def get_item_by_id(self, item_id: int) -> MasterItem | None:
        """Get MasterItem by ID."""
        return (
            self.db.query(MasterItem)
            .filter(MasterItem.id == item_id, MasterItem.is_deleted == False)  # noqa: E712
            .first()
        )

    def get_item_by_type_code(self, item_type: str, code: str) -> MasterItem | None:
        """Get MasterItem by type and unique code."""
        return (
            self.db.query(MasterItem)
            .filter(
                MasterItem.type == item_type.upper(),
                MasterItem.code == code.upper(),
                MasterItem.is_deleted == False,  # noqa: E712
            )
            .first()
        )

    def create_item(
        self,
        item_type: str,
        code: str,
        name: str,
        description: str | None = None,
        sort_order: int = 0,
        created_by_user_id: int | None = None,
    ) -> MasterItem:
        """Create a new MasterItem."""
        item = MasterItem(
            type=item_type.upper(),
            code=code.upper(),
            name=name.strip(),
            description=description.strip() if description else None,
            sort_order=sort_order,
            is_active=True,
            created_by=created_by_user_id,
        )
        self.db.add(item)
        self.db.flush()
        return item

    # States
    def list_states(self, active_only: bool = True) -> list[State]:
        """List all states."""
        query = self.db.query(State).filter(State.is_deleted == False)  # noqa: E712
        if active_only:
            query = query.filter(State.is_active == True)  # noqa: E712
        return query.order_by(State.name.asc()).all()

    def get_state_by_id(self, state_id: int) -> State | None:
        """Get state by primary key ID."""
        return (
            self.db.query(State)
            .filter(State.id == state_id, State.is_deleted == False)  # noqa: E712
            .first()
        )

    def get_state_by_code(self, code: str) -> State | None:
        """Get state by code."""
        return (
            self.db.query(State)
            .filter(State.code == code.upper(), State.is_deleted == False)  # noqa: E712
            .first()
        )

    def create_state(self, name: str, code: str, created_by_user_id: int | None = None) -> State:
        """Create a new State."""
        state = State(
            name=name.strip(),
            code=code.upper().strip(),
            is_active=True,
            created_by=created_by_user_id,
        )
        self.db.add(state)
        self.db.flush()
        return state

    # Cities
    def list_cities(self, state_id: int | None = None, active_only: bool = True) -> list[City]:
        """List cities optionally filtered by state."""
        query = self.db.query(City).filter(City.is_deleted == False)  # noqa: E712
        if state_id is not None:
            query = query.filter(City.state_id == state_id)
        if active_only:
            query = query.filter(City.is_active == True)  # noqa: E712
        return query.order_by(City.name.asc()).all()

    def get_city_by_id(self, city_id: int) -> City | None:
        """Get city by ID."""
        return (
            self.db.query(City)
            .filter(City.id == city_id, City.is_deleted == False)  # noqa: E712
            .first()
        )

    def create_city(
        self,
        state_id: int,
        name: str,
        code: str | None = None,
        created_by_user_id: int | None = None,
    ) -> City:
        """Create a new City under a State."""
        city = City(
            state_id=state_id,
            name=name.strip(),
            code=code.upper().strip() if code else None,
            is_active=True,
            created_by=created_by_user_id,
        )
        self.db.add(city)
        self.db.flush()
        return city

    # Areas
    def list_areas(self, city_id: int | None = None, active_only: bool = True) -> list[Area]:
        """List areas optionally filtered by city."""
        query = self.db.query(Area).filter(Area.is_deleted == False)  # noqa: E712
        if city_id is not None:
            query = query.filter(Area.city_id == city_id)
        if active_only:
            query = query.filter(Area.is_active == True)  # noqa: E712
        return query.order_by(Area.name.asc()).all()

    def get_area_by_id(self, area_id: int) -> Area | None:
        """Get area by ID."""
        return (
            self.db.query(Area)
            .filter(Area.id == area_id, Area.is_deleted == False)  # noqa: E712
            .first()
        )

    def create_area(
        self,
        city_id: int,
        name: str,
        pincode: str | None = None,
        created_by_user_id: int | None = None,
    ) -> Area:
        """Create a new Area under a City."""
        area = Area(
            city_id=city_id,
            name=name.strip(),
            pincode=pincode.strip() if pincode else None,
            is_active=True,
            created_by=created_by_user_id,
        )
        self.db.add(area)
        self.db.flush()
        return area
