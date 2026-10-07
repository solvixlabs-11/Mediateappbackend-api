"""R13 - Follow-up Action Items Report."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.dcr.models import FollowUp
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema


class FollowUpReport(BaseReport):
    """R13 Follow-up.

    Pending, overdue, done follow-ups with days overdue.
    """

    key = "follow_up_report"
    title = "Follow-up Report"
    group = "Customers"
    description = (
        "Doctor feedback commitments, sample deliveries, literature follow-ups, and overdue ageing."
    )
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        status_picker=True,
        status_options=["All", "PENDING", "COMPLETED", "CANCELLED", "OVERDUE"],
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="customer_name", label="Customer", type="string"),
            ReportColumn(key="customer_type", label="Type", type="string"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(
                key="source_visit_date", label="Source Visit Date", type="date", align="center"
            ),
            ReportColumn(key="due_date", label="Due Date", type="date", align="center"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
            ReportColumn(key="days_overdue", label="Days Overdue", type="number", align="right"),
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
            select(FollowUp)
            .options(
                selectinload(FollowUp.user),
                selectinload(FollowUp.doctor),
            )
            .order_by(FollowUp.due_date.asc())
        )

        if user_ids is not None:
            stmt = stmt.where(FollowUp.user_id.in_(user_ids))
        if start_utc and end_utc:
            stmt = stmt.where(
                FollowUp.created_at >= start_utc,
                FollowUp.created_at <= end_utc,
            )

        records = db.scalars(stmt).all()
        today = date.today()
        results: list[dict[str, Any]] = []

        for fu in records:
            cust_name = (
                f"Dr. {fu.doctor.full_name}" if fu.doctor else (fu.title or "Valued Customer")
            )
            is_overdue = fu.status == "PENDING" and fu.due_date < today
            days_ov = (today - fu.due_date).days if is_overdue else 0
            stat_display = "Overdue" if is_overdue else fu.status.title()

            if filters.status and filters.status.lower() != "all":
                if filters.status.lower() == "overdue" and not is_overdue:
                    continue
                if (
                    filters.status.lower() in ["pending", "completed", "cancelled"]
                    and fu.status.lower() != filters.status.lower()
                ):
                    continue

            results.append(
                {
                    "customer_name": cust_name,
                    "customer_type": fu.customer_type.title() if fu.customer_type else "Doctor",
                    "mr_name": fu.user.full_name if fu.user else f"MR #{fu.user_id}",
                    "source_visit_date": fu.created_at.strftime("%Y-%m-%d"),
                    "due_date": fu.due_date.isoformat(),
                    "status": stat_display,
                    "days_overdue": days_ov if days_ov > 0 else None,
                    "_raw_status": "OVERDUE" if is_overdue else fu.status,
                }
            )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(items)
        pending = sum(1 for it in items if it.get("_raw_status") == "PENDING")
        overdue = sum(1 for it in items if it.get("_raw_status") == "OVERDUE")
        done = sum(1 for it in items if it.get("_raw_status") == "COMPLETED")

        return {
            "total_followups": total,
            "pending_count": pending,
            "overdue_count": overdue,
            "done_count": done,
        }


ReportRegistry.register(FollowUpReport)
