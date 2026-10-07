"""R06 - Pending / Late DCR Report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from app.modules.attendance.models import Attendance
from app.modules.dcr.models import DcrVisit, PlannedVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.reports.utils import utc_to_ist_time
from app.modules.users.models import User


class PendingLateDcrReport(BaseReport):
    """R06 Pending / Late DCR.

    Days with check-in but missing or late DCRs.
    """

    key = "pending_late_dcr"
    title = "Pending / Late DCR Report"
    group = "Activity"
    description = (
        "Days with field check-in but missing or late call submissions against planned schedule."
    )
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="check_in_time", label="Check-in Time", type="string", align="center"),
            ReportColumn(
                key="planned_visits", label="Planned Visits", type="number", align="right"
            ),
            ReportColumn(
                key="dcrs_submitted", label="DCRs Submitted", type="number", align="right"
            ),
            ReportColumn(key="gap", label="Gap", type="number", align="right"),
            ReportColumn(
                key="late_submission", label="Late Submission", type="status", align="center"
            ),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
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

            p_count = int(
                db.scalar(
                    select(func.count(PlannedVisit.id)).where(
                        PlannedVisit.user_id == u_id,
                        PlannedVisit.plan_date == att_d,
                    )
                )
                or 0
            )

            d_count = int(
                db.scalar(
                    select(func.count(DcrVisit.id)).where(
                        DcrVisit.user_id == u_id,
                        DcrVisit.dcr_date == att_d,
                    )
                )
                or 0
            )

            gap = max(0, p_count - d_count)

            # Check if any visit was created on next day or later
            late_stmt = select(func.count(DcrVisit.id)).where(
                DcrVisit.user_id == u_id,
                DcrVisit.dcr_date == att_d,
                cast(DcrVisit.created_at, Date) > att_d,
            )
            is_late = int(db.scalar(late_stmt) or 0) > 0

            # Only include if there is a gap or late submission or no visits submitted
            if gap > 0 or is_late or d_count == 0:
                results.append(
                    {
                        "date": att_d.isoformat(),
                        "mr_name": user_name,
                        "check_in_time": utc_to_ist_time(att.check_in_time),
                        "planned_visits": p_count,
                        "dcrs_submitted": d_count,
                        "gap": gap,
                        "late_submission": "Yes" if is_late else "No",
                        "_raw_gap": gap,
                    }
                )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        days_with_gaps = len(items)
        total_gaps = sum(int(it.get("_raw_gap", 0)) for it in items)

        return {
            "days_with_gaps": days_with_gaps,
            "total_gaps": total_gaps,
        }


ReportRegistry.register(PendingLateDcrReport)
