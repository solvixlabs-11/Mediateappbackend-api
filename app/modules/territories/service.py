"""Territory business logic service."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.territories.repository import TerritoryRepository
from app.modules.territories.schemas import (
    AssignTerritoryRequest,
    TerritoryAssignmentResponse,
    TerritoryCreate,
    TerritoryResponse,
    TerritoryUpdate,
)
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class TerritoryService:
    """Service handling territory definitions and user assignment."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TerritoryRepository(db)
        self.user_repo = UserRepository(db)

    def list_territories(
        self,
        search: str | None = None,
        state_id: int | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[TerritoryResponse]:
        """Fetch territory list."""
        territories = self.repo.list_territories(
            search=search,
            state_id=state_id,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )
        return [TerritoryResponse.model_validate(t) for t in territories]

    def get_territory_by_id(self, territory_id: int) -> TerritoryResponse:
        """Fetch territory by ID."""
        territory = self.repo.get_by_id(territory_id)
        if not territory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Territory with ID {territory_id} not found",
            )
        return TerritoryResponse.model_validate(territory)

    def create_territory(self, payload: TerritoryCreate, current_user: User) -> TerritoryResponse:
        """Create new territory (Admin only)."""
        existing = self.repo.get_by_code(payload.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Territory with code '{payload.code}' already exists",
            )

        territory = self.repo.create(
            name=payload.name,
            code=payload.code,
            headquarters=payload.headquarters,
            state_id=payload.state_id,
            description=payload.description,
            area_ids=payload.area_ids,
            created_by_user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(territory)
        return TerritoryResponse.model_validate(territory)

    def update_territory(
        self, territory_id: int, payload: TerritoryUpdate, current_user: User
    ) -> TerritoryResponse:
        """Update existing territory."""
        territory = self.repo.get_by_id(territory_id)
        if not territory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Territory with ID {territory_id} not found",
            )

        if payload.name is not None:
            territory.name = payload.name.strip()
        if payload.headquarters is not None:
            territory.headquarters = payload.headquarters.strip()
        if payload.state_id is not None:
            territory.state_id = payload.state_id
        if payload.description is not None:
            territory.description = payload.description.strip()
        if payload.is_active is not None:
            territory.is_active = payload.is_active
        if payload.area_ids is not None:
            self.repo.update_areas(territory, payload.area_ids)

        territory.updated_by = current_user.id
        self.db.commit()
        self.db.refresh(territory)
        return TerritoryResponse.model_validate(territory)

    def assign_user(
        self, territory_id: int, payload: AssignTerritoryRequest, current_user: User
    ) -> TerritoryAssignmentResponse:
        """Assign user to a territory."""
        territory = self.repo.get_by_id(territory_id)
        if not territory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Territory with ID {territory_id} not found",
            )

        target_user = self.user_repo.get_by_id(payload.user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {payload.user_id} not found",
            )

        assignment = self.repo.assign_user(
            user_id=target_user.id,
            territory_id=territory.id,
            created_by_user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(assignment)

        return TerritoryAssignmentResponse(
            id=assignment.id,
            user_id=target_user.id,
            user_name=target_user.full_name,
            territory_id=territory.id,
            territory_name=territory.name,
            assigned_at=assignment.assigned_at,
            unassigned_at=assignment.unassigned_at,
            is_active=assignment.unassigned_at is None,
        )

    def unassign_user(self, territory_id: int, user_id: int, current_user: User) -> dict[str, str]:
        """Unassign user from a territory."""
        success = self.repo.unassign_user(
            user_id=user_id, territory_id=territory_id, updated_by_user_id=current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active assignment not found",
            )
        self.db.commit()
        return {"message": "User unassigned from territory successfully"}

    def get_my_territories(self, current_user: User) -> list[TerritoryResponse]:
        """Fetch current user's active assigned territories."""
        territories = self.repo.get_user_territories(current_user.id)
        return [TerritoryResponse.model_validate(t) for t in territories]
