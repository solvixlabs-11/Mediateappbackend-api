"""Tour Program database repository."""

from __future__ import annotations

from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.tours.models import TourProgram


class TourRepository:
    """Repository handling Tour Program persistence and overlap queries."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, tour_id: int) -> TourProgram | None:
        """Fetch tour program by id."""
        return self.db.query(TourProgram).filter(TourProgram.id == tour_id).first()

    def has_overlapping_tour(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        exclude_id: int | None = None,
    ) -> bool:
        """Check if an active tour already exists overlapping this date window (BR-09)."""
        query = self.db.query(TourProgram).filter(
            TourProgram.user_id == user_id,
            TourProgram.status.in_(("SUBMITTED", "APPROVED")),
            or_(
                # New tour starts during existing tour
                TourProgram.start_date.between(start_date, end_date),
                # New tour ends during existing tour
                TourProgram.end_date.between(start_date, end_date),
                # Existing tour falls completely within new tour
                (TourProgram.start_date <= start_date) & (TourProgram.end_date >= end_date),
            ),
        )
        if exclude_id:
            query = query.filter(TourProgram.id != exclude_id)
        return query.first() is not None

    def create(
        self,
        user_id: int,
        title: str,
        start_date: date,
        end_date: date,
        total_days: int,
        route_details: str | None = None,
        objectives: str | None = None,
    ) -> TourProgram:
        """Create a new Tour Program."""
        tour = TourProgram(
            user_id=user_id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            route_details=route_details,
            objectives=objectives,
            status="SUBMITTED",
        )
        self.db.add(tour)
        self.db.flush()
        return tour

    def list_tours(self, user_id: int | None = None) -> list[TourProgram]:
        """List tours with optional user filtering."""
        query = self.db.query(TourProgram)
        if user_id:
            query = query.filter(TourProgram.user_id == user_id)
        return query.order_by(TourProgram.start_date.desc()).all()
