"""R14 - Approval Turnaround Report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.approvals.models import ApprovalHistory, ApprovalRequest
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.reports.utils import utc_to_ist_date, utc_to_ist_str


class ApprovalTurnaroundReport(BaseReport):
    """R14 Approval Turnaround.

    Time taken per approval, pending ageing, average hours.
    """

    key = "approval_turnaround"
    title = "Approval Turnaround Report"
    group = "Approvals"
    description = "Time taken for managerial decisions across tours, leaves, and expenses, approval ageing, and SLA turnaround."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        status_picker=True,
        status_options=["All", "PENDING", "APPROVED", "REJECTED"],
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="request_type", label="Request Type", type="string"),
            ReportColumn(key="requester", label="Requester", type="string"),
            ReportColumn(key="submitted_on", label="Submitted On", type="date", align="center"),
            ReportColumn(key="current_step", label="Step / Level", type="string"),
            ReportColumn(key="approver", label="Approver", type="string"),
            ReportColumn(key="action", label="Action", type="status", align="center"),
            ReportColumn(key="action_time", label="Action Time", type="string", align="center"),
            ReportColumn(key="hours_taken", label="Hours Taken", type="number", align="right"),
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
            select(ApprovalRequest)
            .options(
                selectinload(ApprovalRequest.requester),
                selectinload(ApprovalRequest.history).selectinload(ApprovalHistory.approver),
            )
            .order_by(ApprovalRequest.created_at.desc())
        )

        if user_ids is not None:
            stmt = stmt.where(ApprovalRequest.requester_id.in_(user_ids))
        if start_utc and end_utc:
            stmt = stmt.where(
                ApprovalRequest.created_at >= start_utc,
                ApprovalRequest.created_at <= end_utc,
            )
        if filters.status and filters.status.lower() != "all":
            stmt = stmt.where(ApprovalRequest.status == filters.status.upper())

        records = db.scalars(stmt).all()
        now = datetime.utcnow()
        results: list[dict[str, Any]] = []

        for req in records:
            last_action = req.history[-1] if req.history else None
            hours_taken: float = 0.0

            if last_action and last_action.decided_at:
                diff_sec = (last_action.decided_at - req.created_at).total_seconds()
                hours_taken = round(max(0.1, diff_sec / 3600.0), 1)
            else:
                diff_sec = (now - req.created_at).total_seconds()
                hours_taken = round(max(0.1, diff_sec / 3600.0), 1)

            approver_name = (
                last_action.approver.full_name
                if last_action and last_action.approver
                else ("Branch Manager" if req.status == "PENDING" else "-")
            )
            action_name = last_action.decision if last_action else "-"
            action_time_str = utc_to_ist_str(last_action.decided_at) if last_action else "-"

            is_over_24h = req.status == "PENDING" and hours_taken > 24.0

            results.append(
                {
                    "request_type": req.entity_type.replace("_", " ").title(),
                    "requester": req.requester.full_name
                    if req.requester
                    else f"User #{req.requester_id}",
                    "submitted_on": utc_to_ist_date(req.created_at),
                    "current_step": f"Level {req.current_step or 1}",
                    "approver": approver_name,
                    "action": action_name,
                    "action_time": action_time_str,
                    "hours_taken": hours_taken,
                    "status": req.status.title(),
                    "_raw_hours": hours_taken,
                    "_raw_over_24h": is_over_24h,
                }
            )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(items)
        if total == 0:
            return {
                "total_approvals": 0,
                "average_hours": 0.0,
                "pending_over_24h": 0,
            }

        total_hours = sum(float(it.get("_raw_hours", 0.0)) for it in items)
        avg_hours = round(total_hours / total, 1)
        over_24 = sum(1 for it in items if it.get("_raw_over_24h"))

        return {
            "total_approvals": total,
            "average_hours": avg_hours,
            "pending_over_24h": over_24,
        }


ReportRegistry.register(ApprovalTurnaroundReport)
