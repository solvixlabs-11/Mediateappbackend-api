"""R09 - Attendance Report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.attendance.models import Attendance
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.reports.utils import utc_to_ist_time
from app.modules.users.models import User


class AttendanceReport(BaseReport):
    """R09 Attendance.

    Check-in/out time and place, hours, late, absent, leave.
    """

    key = "attendance"
    title = "Attendance Report"
    group = "HR and Expense"
    description = "Daily shift check-in and check-out logs, geocoded locations, shift durations, late arrivals, and status."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        status_picker=True,
        status_options=["All", "Present", "Late", "Absent", "On Leave"],
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="work_type", label="Work Type", type="string"),
            ReportColumn(key="check_in_time", label="Check-in Time", type="string", align="center"),
            ReportColumn(key="check_in_place", label="Check-in Place", type="string"),
            ReportColumn(
                key="check_out_time", label="Check-out Time", type="string", align="center"
            ),
            ReportColumn(key="check_out_place", label="Check-out Place", type="string"),
            ReportColumn(key="hours", label="Hours", type="number", align="right"),
            ReportColumn(key="is_late", label="Late Arrival", type="status", align="center"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(Attendance, User.full_name)
            .join(User, Attendance.user_id == User.id)
            .order_by(Attendance.date.desc(), User.full_name)
        )

        if user_ids is not None:
            stmt = stmt.where(Attendance.user_id.in_(user_ids))
        if start_utc and end_utc:
            stmt = stmt.where(
                Attendance.check_in_time >= start_utc,
                Attendance.check_in_time <= end_utc,
            )

        records = db.execute(stmt).all()
        results: list[dict[str, Any]] = []

        for att, user_name in records:
            # Late logic: check-in after 09:30 AM IST (04:00 UTC)
            is_late_arrival = False
            if att.check_in_time:
                ist_hour = (att.check_in_time.hour + 5 + (att.check_in_time.minute + 30) // 60) % 24
                ist_minute = (att.check_in_time.minute + 30) % 60
                if ist_hour > 9 or (ist_hour == 9 and ist_minute > 30):
                    is_late_arrival = True

            hours_val = round((att.total_work_minutes or 0) / 60.0, 1)
            stat = att.status or "PRESENT"

            if filters.status and filters.status.lower() != "all":
                if filters.status.lower() == "late" and not is_late_arrival:
                    continue
                if (
                    filters.status.lower() in ["present", "on leave"]
                    and stat.lower() != filters.status.lower()
                ):
                    continue

            results.append(
                {
                    "date": att.date.isoformat(),
                    "mr_name": user_name,
                    "work_type": att.status or "FIELD_WORK",
                    "check_in_time": utc_to_ist_time(att.check_in_time),
                    "check_in_place": att.check_in_address or "GPS Verified Location",
                    "check_out_time": utc_to_ist_time(att.check_out_time)
                    if att.check_out_time
                    else "-",
                    "check_out_place": att.check_out_address
                    or ("-" if not att.check_out_time else "GPS Location"),
                    "hours": hours_val,
                    "is_late": "Yes" if is_late_arrival else "No",
                    "status": "Late" if is_late_arrival else stat.title(),
                    "_raw_status": stat,
                    "_raw_late": is_late_arrival,
                }
            )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(items)
        present = sum(
            1 for it in items if it.get("_raw_status") in ["PRESENT", "CHECKED_IN", "CHECKED_OUT"]
        )
        late = sum(1 for it in items if it.get("_raw_late"))
        leave = sum(1 for it in items if it.get("_raw_status") in ["LEAVE", "ON_LEAVE"])
        absent = total - present - leave

        return {
            "present_count": present,
            "late_count": late,
            "leave_count": leave,
            "absent_count": max(0, absent),
        }


ReportRegistry.register(AttendanceReport)
