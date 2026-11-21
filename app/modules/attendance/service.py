

"""Attendance business logic service."""

from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.attendance.models import Attendance
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.schemas import (
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    AttendanceResponse,
)
from app.modules.audit.service import AuditService
from app.modules.settings.service import SettingsService
from app.modules.users.models import User


class AttendanceService:
    """Service enforcing BR-02 (one check-in per day, check-out only after check-in)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AttendanceRepository(db)

    def _map_response(self, record: Attendance | None, user: User | None = None) -> AttendanceResponse | None:
        if not record:
            return None
        res = AttendanceResponse.model_validate(record)
        u = user or (record.user if hasattr(record, "user") else None)
        if u:
            res.user_name = u.full_name
            res.employee_code = u.employee_code
        return res

    def get_today_attendance(self, user: User) -> AttendanceResponse | None:
        """Fetch today's attendance for the logged-in user."""
        today = date.today()
        record = self.repo.get_by_date(user.id, today)
        return self._map_response(record, user)

    def check_in(self, payload: AttendanceCheckInRequest, user: User) -> AttendanceResponse:
        """Record morning check-in with GPS validation."""
        target_date = payload.date or date.today()

        # Idempotency check with client_uuid
        if payload.client_uuid:
            existing_uuid = self.repo.get_by_client_uuid(payload.client_uuid)
            if existing_uuid:
                mapped = self._map_response(existing_uuid, user)
                if mapped:
                    return mapped

        # Check existing attendance for target date (BR-02)
        existing = self.repo.get_by_date(user.id, target_date)
        if existing and existing.check_in_time:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance check-in already recorded for {target_date}.",
            )

        # Enforce mock GPS policy via SettingsService
        settings_svc = SettingsService(self.db)
        if payload.mock_location_flag:
            mock_action = settings_svc.get_setting_value("gps.mock_location_action", "FLAG").upper().strip()
            if mock_action == "BLOCK":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Check-in failed: Mock location detected and blocked by security policy.",
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
        AuditService.record(
            self.db,
            user_id=user.id,
            module="ATTENDANCE",
            action="CREATE",
            entity_type="Attendance",
            entity_id=str(attendance.id),
            summary=f"Check-in recorded for {user.full_name} at {now.strftime('%H:%M:%S')} (mock={payload.mock_location_flag})",
            channel="MOBILE",
        )
        self.db.commit()
        self.db.refresh(attendance)
        res = self._map_response(attendance, user)
        if not res:
            raise HTTPException(status_code=500, detail="Failed to map attendance")
        return res

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
            mapped = self._map_response(existing, user)
            if mapped:
                return mapped

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
        res = self._map_response(attendance, user)
        if not res:
            raise HTTPException(status_code=500, detail="Failed to map attendance")
        return res

    def list_history(
        self,
        current_user: User,
        user_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AttendanceResponse]:
        """Fetch attendance log with role-based scoping."""
        is_admin_or_mgr = bool(
            current_user.role and current_user.role.code in ("ADMIN", "MANAGER", "SUPERADMIN", "ERP ADMIN")
        )

        effective_user_id: int | None
        if is_admin_or_mgr:
            effective_user_id = user_id
        else:
            effective_user_id = current_user.id

        records = self.repo.list_history(
            user_id=effective_user_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
        responses: list[AttendanceResponse] = []
        for r in records:
            res = AttendanceResponse.model_validate(r)
            if r.user:
                res.user_name = r.user.full_name
                res.employee_code = r.user.employee_code
            responses.append(res)
        return responses
