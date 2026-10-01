"""Attendance database repository."""

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.modules.attendance.models import Attendance


class AttendanceRepository:
    """Repository handling daily check-in and check-out records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_date(self, user_id: int, target_date: date) -> Attendance | None:
        """Fetch attendance for specific user and date."""
        return (
            self.db.query(Attendance)
            .filter(Attendance.user_id == user_id, Attendance.date == target_date)
            .first()
        )

    def get_by_client_uuid(self, client_uuid: str) -> Attendance | None:
        """Fetch attendance record by idempotent client_uuid."""
        return self.db.query(Attendance).filter(Attendance.client_uuid == client_uuid).first()

    def create_check_in(
        self,
        user_id: int,
        target_date: date,
        check_in_time: datetime,
        latitude: float,
        longitude: float,
        accuracy: float | None = None,
        address: str | None = None,
        mock_flag: bool = False,
        remarks: str | None = None,
        client_uuid: str | None = None,
    ) -> Attendance:
        """Create new daily check-in."""
        attendance = Attendance(
            user_id=user_id,
            date=target_date,
            status="PRESENT",
            check_in_time=check_in_time,
            check_in_latitude=latitude,
            check_in_longitude=longitude,
            check_in_accuracy=accuracy,
            check_in_address=address,
            check_in_mock_flag=mock_flag,
            remarks=remarks,
            client_uuid=client_uuid,
        )
        self.db.add(attendance)
        self.db.flush()
        return attendance

    def record_check_out(
        self,
        attendance: Attendance,
        check_out_time: datetime,
        latitude: float,
        longitude: float,
        accuracy: float | None = None,
        address: str | None = None,
        mock_flag: bool = False,
        remarks: str | None = None,
    ) -> Attendance:
        """Update attendance with check-out and work minutes."""
        attendance.check_out_time = check_out_time
        attendance.check_out_latitude = latitude
        attendance.check_out_longitude = longitude
        attendance.check_out_accuracy = accuracy
        attendance.check_out_address = address
        attendance.check_out_mock_flag = mock_flag

        if attendance.check_in_time:
            diff = check_out_time - attendance.check_in_time
            attendance.total_work_minutes = max(0, int(diff.total_seconds() / 60))

        if remarks:
            attendance.remarks = (
                f"{attendance.remarks}\n{remarks}" if attendance.remarks else remarks
            )

        self.db.flush()
        return attendance

    def list_history(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        skip: int = 0,
        limit: int = 31,
    ) -> list[Attendance]:
        """Fetch chronological attendance records for user."""
        query = self.db.query(Attendance).filter(Attendance.user_id == user_id)
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        return query.order_by(Attendance.date.desc()).offset(skip).limit(limit).all()
