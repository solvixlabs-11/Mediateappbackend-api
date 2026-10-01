"""Territory database repository."""

from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.mixins import utc_now
from app.modules.masters.models import Area
from app.modules.territories.models import Territory, UserTerritoryAssignment


class TerritoryRepository:
    """Repository handling territory CRUD and user allocations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_territories(
        self,
        search: str | None = None,
        state_id: int | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Territory]:
        """Fetch filtered territories."""
        query = (
            self.db.query(Territory)
            .options(selectinload(Territory.areas))
            .filter(Territory.is_deleted == False)  # noqa: E712
        )
        if active_only:
            query = query.filter(Territory.is_active == True)  # noqa: E712
        if state_id is not None:
            query = query.filter(Territory.state_id == state_id)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                Territory.name.ilike(pattern)
                | Territory.code.ilike(pattern)
                | Territory.headquarters.ilike(pattern)
            )

        return query.order_by(Territory.name.asc()).offset(skip).limit(limit).all()

    def get_by_id(self, territory_id: int) -> Territory | None:
        """Fetch territory by ID."""
        return (
            self.db.query(Territory)
            .options(selectinload(Territory.areas))
            .filter(Territory.id == territory_id, Territory.is_deleted == False)  # noqa: E712
            .first()
        )

    def get_by_code(self, code: str) -> Territory | None:
        """Fetch territory by unique code."""
        return (
            self.db.query(Territory)
            .filter(Territory.code == code.upper(), Territory.is_deleted == False)  # noqa: E712
            .first()
        )

    def create(
        self,
        name: str,
        code: str,
        headquarters: str,
        state_id: int | None = None,
        description: str | None = None,
        area_ids: list[int] | None = None,
        created_by_user_id: int | None = None,
    ) -> Territory:
        """Create a new Territory and bind area mappings."""
        territory = Territory(
            name=name.strip(),
            code=code.upper().strip(),
            headquarters=headquarters.strip(),
            state_id=state_id,
            description=description.strip() if description else None,
            is_active=True,
            created_by=created_by_user_id,
        )
        if area_ids:
            areas = (
                self.db.query(Area)
                .filter(Area.id.in_(area_ids), Area.is_deleted == False)  # noqa: E712
                .all()
            )
            territory.areas = areas

        self.db.add(territory)
        self.db.flush()
        return territory

    def update_areas(self, territory: Territory, area_ids: list[int]) -> None:
        """Replace mapped areas for a territory."""
        areas = (
            self.db.query(Area)
            .filter(Area.id.in_(area_ids), Area.is_deleted == False)  # noqa: E712
            .all()
        )
        territory.areas = areas
        self.db.flush()

    # User Assignments
    def get_active_assignment(
        self, user_id: int, territory_id: int
    ) -> UserTerritoryAssignment | None:
        """Find active assignment between user and territory."""
        return (
            self.db.query(UserTerritoryAssignment)
            .filter(
                UserTerritoryAssignment.user_id == user_id,
                UserTerritoryAssignment.territory_id == territory_id,
                UserTerritoryAssignment.unassigned_at.is_(None),
                UserTerritoryAssignment.is_deleted == False,  # noqa: E712
            )
            .first()
        )

    def assign_user(
        self,
        user_id: int,
        territory_id: int,
        created_by_user_id: int | None = None,
    ) -> UserTerritoryAssignment:
        """Assign user to territory."""
        existing = self.get_active_assignment(user_id, territory_id)
        if existing:
            return existing

        assignment = UserTerritoryAssignment(
            user_id=user_id,
            territory_id=territory_id,
            assigned_at=utc_now(),
            unassigned_at=None,
            created_by=created_by_user_id,
        )
        self.db.add(assignment)
        self.db.flush()
        return assignment

    def unassign_user(
        self,
        user_id: int,
        territory_id: int,
        updated_by_user_id: int | None = None,
    ) -> bool:
        """Close active assignment."""
        assignment = self.get_active_assignment(user_id, territory_id)
        if assignment:
            assignment.unassigned_at = utc_now()
            assignment.updated_by = updated_by_user_id
            self.db.flush()
            return True
        return False

    def get_user_territories(self, user_id: int) -> list[Territory]:
        """Fetch all currently active territories assigned to a user."""
        assignments = (
            self.db.query(UserTerritoryAssignment)
            .options(joinedload(UserTerritoryAssignment.territory))
            .filter(
                UserTerritoryAssignment.user_id == user_id,
                UserTerritoryAssignment.unassigned_at.is_(None),
                UserTerritoryAssignment.is_deleted == False,  # noqa: E712
            )
            .all()
        )
        return [a.territory for a in assignments if a.territory and a.territory.is_active]
