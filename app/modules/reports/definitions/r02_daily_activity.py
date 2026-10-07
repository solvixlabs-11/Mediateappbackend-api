"""R02 - Daily Activity Summary Report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.attendance.models import Attendance
from app.modules.dcr.models import DcrVisit, PlannedVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.reports.utils import utc_to_ist_time
from app.modules.users.models import User


class DailyActivityReport(BaseReport):
    """R02 Daily Activity Summary.

    One row per MR per day: check-in/out, hours, calls by type, planned vs done.
    """

    key = "daily_activity"
    title = "Daily Activity Summary"
    group = "Activity"
    description = "One row per MR per day: check-in/out, hours, calls by type, planned vs done."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        status_picker=False,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="work_type", label="Work Type", type="string"),
            ReportColumn(key="check_in", label="Check-in", type="string", align="center"),
            ReportColumn(key="check_out", label="Check-out", type="string", align="center"),
            ReportColumn(key="hours", label="Hours", type="number", align="right"),
            ReportColumn(key="calls_total", label="Calls Total", type="number", align="right"),
            ReportColumn(key="doctors", label="Doctors", type="number", align="right"),
            ReportColumn(key="hospitals", label="Hospitals", type="number", align="right"),
            ReportColumn(key="chemists", label="Chemists", type="number", align="right"),
            ReportColumn(key="stockists", label="Stockists", type="number", align="right"),
            ReportColumn(key="planned", label="Planned", type="number", align="right"),
            ReportColumn(key="missed", label="Missed", type="number", align="right"),
            ReportColumn(key="dcr_submitted", label="DCR Submitted", type="status", align="center"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        # Fetch attendance records within range
        att_stmt = select(Attendance, User.full_name).join(User, Attendance.user_id == User.id)
        if user_ids is not None:
            att_stmt = att_stmt.where(Attendance.user_id.in_(user_ids))
        if start_utc and end_utc:
            att_stmt = att_stmt.where(
                Attendance.check_in_time >= start_utc,
                Attendance.check_in_time <= end_utc,
            )
        att_stmt = att_stmt.order_by(Attendance.date.desc(), Attendance.user_id)
        att_records = db.execute(att_stmt).all()

        results: list[dict[str, Any]] = []

        for att, user_name in att_records:
            u_id = att.user_id
            att_d = att.date

            # Calls breakdown on this day
            v_stmt = (
                select(
                    DcrVisit.customer_type,
                    func.count(DcrVisit.id),
                )
                .where(
                    DcrVisit.user_id == u_id,
                    DcrVisit.dcr_date == att_d,
                )
                .group_by(DcrVisit.customer_type)
            )

            v_counts = dict(db.execute(v_stmt).all())
            docs = v_counts.get("DOCTOR", 0)
            chem = v_counts.get("CHEMIST", 0)
            hosp = v_counts.get("HOSPITAL", 0)
            stock = v_counts.get("STOCKIST", 0)
            total_calls = sum(v_counts.values())

            # Planned visits on this day
            p_stmt = select(
                func.count(PlannedVisit.id),
                func.sum(func.case((PlannedVisit.status == "MISSED", 1), else_=0)),
            ).where(
                PlannedVisit.user_id == u_id,
                PlannedVisit.plan_date == att_d,
            )
            planned_row = db.execute(p_stmt).first()
            planned_count = int(planned_row[0] or 0) if planned_row else 0
            missed_count = int(planned_row[1] or 0) if planned_row else 0

            hours_val = round((att.total_work_minutes or 0) / 60.0, 1)

            results.append(
                {
                    "date": att_d.isoformat(),
                    "mr_name": user_name,
                    "work_type": att.status or "FIELD_WORK",
                    "check_in": utc_to_ist_time(att.check_in_time),
                    "check_out": utc_to_ist_time(att.check_out_time) if att.check_out_time else "-",
                    "hours": hours_val,
                    "calls_total": total_calls,
                    "doctors": docs,
                    "hospitals": hosp,
                    "chemists": chem,
                    "stockists": stock,
                    "planned": planned_count,
                    "missed": missed_count,
                    "dcr_submitted": "Yes" if total_calls > 0 else "No",
                    "_raw_hours": hours_val,
                    "_raw_calls": total_calls,
                }
            )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        days_worked = len(items)
        if days_worked == 0:
            return {
                "days_worked": 0,
                "total_calls": 0,
                "average_calls_per_day": 0.0,
                "average_hours": 0.0,
            }

        total_calls = sum(int(it.get("_raw_calls", 0)) for it in items)
        total_hours = sum(float(it.get("_raw_hours", 0.0)) for it in items)
        avg_calls = round(total_calls / days_worked, 1)
        avg_hours = round(total_hours / days_worked, 1)

        return {
            "days_worked": days_worked,
            "total_calls": total_calls,
            "average_calls_per_day": avg_calls,
            "average_hours": avg_hours,
        }


ReportRegistry.register(DailyActivityReport)
