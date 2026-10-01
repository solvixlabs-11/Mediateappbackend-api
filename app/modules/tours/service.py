"""Tour Program business logic service."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.approvals.repository import ApprovalRepository
from app.modules.tours.models import TourProgram
from app.modules.tours.repository import TourRepository
from app.modules.tours.schemas import TourProgramCreateRequest, TourProgramResponse
from app.modules.users.models import User


class TourService:
    """Service enforcing Tour Program lifecycle and approval dispatch."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TourRepository(db)
        self.approval_repo = ApprovalRepository(db)

    def _to_response(self, tour: TourProgram) -> TourProgramResponse:
        return TourProgramResponse(
            id=tour.id,
            user_id=tour.user_id,
            user_name=tour.user.full_name if tour.user else None,
            title=tour.title,
            start_date=tour.start_date,
            end_date=tour.end_date,
            total_days=tour.total_days,
            route_details=tour.route_details,
            objectives=tour.objectives,
            status=tour.status,
            approval_request_id=tour.approval_request_id,
            rejection_reason=tour.rejection_reason,
            created_at=tour.created_at,
            updated_at=tour.updated_at,
        )

    def create_tour(self, payload: TourProgramCreateRequest, user: User) -> TourProgramResponse:
        """Create and submit a Tour Program with overlap validation (BR-09)."""
        if payload.end_date < payload.start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tour end date cannot precede start date.",
            )

        # BR-09: Overlapping tour check
        if self.repo.has_overlapping_tour(user.id, payload.start_date, payload.end_date):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A Tour Program already exists overlapping this date period.",
            )

        total_days = (payload.end_date - payload.start_date).days + 1

        tour = self.repo.create(
            user_id=user.id,
            title=payload.title,
            start_date=payload.start_date,
            end_date=payload.end_date,
            total_days=total_days,
            route_details=payload.route_details,
            objectives=payload.objectives,
        )

        # Dispatch approval request into the manager's inbox
        approval_req = self.approval_repo.create_request(
            entity_type="TOUR",
            entity_id=tour.id,
            requester_id=user.id,
            title=f"Tour Plan: {tour.title} ({tour.start_date} to {tour.end_date})",
            details=f"Route: {tour.route_details or 'N/A'}. Total Days: {total_days}.",
        )
        tour.approval_request_id = approval_req.id

        self.db.commit()
        self.db.refresh(tour)
        return self._to_response(tour)

    def list_tours(self, current_user: User) -> list[TourProgramResponse]:
        """List tours scoped to user (MR sees own, Manager/Admin sees team/all)."""
        role_code = current_user.role.code if current_user.role else "MR"
        user_id = None if role_code in ("ADMIN", "MANAGER") else current_user.id
        tours = self.repo.list_tours(user_id=user_id)
        return [self._to_response(t) for t in tours]

    def get_tour(self, tour_id: int) -> TourProgramResponse:
        """Fetch tour program by id."""
        tour = self.repo.get_by_id(tour_id)
        if not tour:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tour program {tour_id} not found.",
            )
        return self._to_response(tour)
