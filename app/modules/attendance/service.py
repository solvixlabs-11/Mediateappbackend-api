"""Attendance business logic service."""

from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.schemas import (
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    AttendanceResponse,
)
from app.modules.users.models import User


class AttendanceService:
    """Service enforcing BR-02 (one check-in per day, check-out only after check-in)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AttendanceRepository(db)

    def get_today_attendance(self, user: User) -> AttendanceResponse | None:
        """Fetch today's attendance for the logged-in user."""
        today = date.today()
        record = self.repo.get_by_date(user.id, today)
        if not record:
            return None
        return AttendanceResponse.model_validate(record)

    def check_in(self, payload: AttendanceCheckInRequest, user: User) -> AttendanceResponse:
        """Record morning check-in with GPS validation."""
        target_date = payload.date or date.today()

        # Idempotency check with client_uuid
        if payload.client_uuid:
            existing_uuid = self.repo.get_by_client_uuid(payload.client_uuid)
            if existing_uuid:
                return AttendanceResponse.model_validate(existing_uuid)

        # Check existing attendance for target date (BR-02)
        existing = self.repo.get_by_date(user.id, target_date)
        if existing and existing.check_in_time:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance check-in already recorded for {target_date}.",
            )

        now = datetime.utcnow()
        attendance = self.repo.create_check_in(
            user_id=user.id,
            target_date=target_date,
            check_in_time=now,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy=payload.accuracy,
            address=payload.address,
            mock_flag=payload.mock_location_flag,
            remarks=payload.remarks,
            client_uuid=payload.client_uuid,
        )
        self.db.commit()
        self.db.refresh(attendance)
        return AttendanceResponse.model_validate(attendance)

    def check_out(self, payload: AttendanceCheckOutRequest, user: User) -> AttendanceResponse:
        """Record end-of-day check-out."""
        today = date.today()
        existing = self.repo.get_by_date(user.id, today)
        if not existing or not existing.check_in_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot check out without checking in first.",
            )

        if existing.check_out_time:
            # Return already finalized record idempotently
            return AttendanceResponse.model_validate(existing)

        now = datetime.utcnow()
        attendance = self.repo.record_check_out(
            attendance=existing,
            check_out_time=now,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy=payload.accuracy,
            address=payload.address,
            mock_flag=payload.mock_location_flag,
            remarks=payload.remarks,
        )
        self.db.commit()
        self.db.refresh(attendance)
        return AttendanceResponse.model_validate(attendance)

    def list_history(
        self,
        user: User,
        start_date: date | None = None,
        end_date: date | None = None,
        skip: int = 0,
        limit: int = 31,
    ) -> list[AttendanceResponse]:
        """Fetch attendance log."""
        records = self.repo.list_history(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
        return [AttendanceResponse.model_validate(r) for r in records]
