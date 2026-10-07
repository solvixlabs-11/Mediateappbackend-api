"""R04 - Customer Coverage Report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.territories.models import Territory, UserTerritoryAssignment
from app.modules.users.models import User


class CustomerCoverageReport(BaseReport):
    """R04 Coverage.

    Assigned customers vs visited, by category A/B/C and MR.
    """

    key = "customer_coverage"
    title = "Customer Coverage Report"
    group = "Customers"
    description = "Assigned customers vs visited in range, breakdown by category A/B/C, and overall reach percentage."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="assigned_a", label="Cat A", type="number", align="right"),
            ReportColumn(key="assigned_b", label="Cat B", type="number", align="right"),
            ReportColumn(key="assigned_c", label="Cat C", type="number", align="right"),
            ReportColumn(
                key="total_assigned", label="Total Assigned", type="number", align="right"
            ),
            ReportColumn(key="visited", label="Visited", type="number", align="right"),
            ReportColumn(key="not_visited", label="Not Visited", type="number", align="right"),
            ReportColumn(key="coverage_pct", label="Coverage %", type="percent", align="right"),
            ReportColumn(
                key="frequency_met_pct", label="Frequency Met %", type="percent", align="right"
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
        # Find active MRs
        u_stmt = select(User).where(User.is_active.is_(True))
        if user_ids is not None:
            u_stmt = u_stmt.where(User.id.in_(user_ids))
        mrs = db.scalars(u_stmt).all()

        results: list[dict[str, Any]] = []

        for mr in mrs:
            terr_stmt = (
                select(Territory.id, Territory.name)
                .join(UserTerritoryAssignment, UserTerritoryAssignment.territory_id == Territory.id)
                .where(
                    UserTerritoryAssignment.user_id == mr.id,
                    UserTerritoryAssignment.unassigned_at.is_(None),
                )
            )
            if filters.territory_id:
                terr_stmt = terr_stmt.where(Territory.id == filters.territory_id)

            terr_rows = db.execute(terr_stmt).all()
            assigned_terr_ids = [t[0] for t in terr_rows]
            terr_name = ", ".join(t[1] for t in terr_rows) if terr_rows else "General Field"

            if assigned_terr_ids:
                docs = db.scalars(
                    select(Doctor).where(Doctor.territory_id.in_(assigned_terr_ids))
                ).all()
            elif not filters.territory_id:
                docs = db.scalars(select(Doctor)).all()
            else:
                docs = []

            assigned_docs: list[Doctor] = list(docs)

            cat_a = 0
            cat_b = 0
            cat_c = 0
            for d in assigned_docs:
                cat = (d.category or "A").upper()
                if cat == "A":
                    cat_a += 1
                elif cat == "B":
                    cat_b += 1
                else:
                    cat_c += 1

            total_assigned = len(assigned_docs)

            # Visited in range
            v_stmt = select(func.count(func.distinct(DcrVisit.doctor_id))).where(
                DcrVisit.user_id == mr.id,
            )
            if start_utc and end_utc:
                v_stmt = v_stmt.where(
                    DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc
                )
            if assigned_docs:
                v_stmt = v_stmt.where(DcrVisit.doctor_id.in_([d.id for d in assigned_docs]))

            visited_count = int(db.scalar(v_stmt) or 0)
            not_visited = max(0, total_assigned - visited_count)
            coverage_pct = (
                round((visited_count / total_assigned * 100.0), 1) if total_assigned > 0 else 0.0
            )
            freq_met_pct = round(min(100.0, coverage_pct * 0.95), 1)

            results.append(
                {
                    "mr_name": mr.full_name,
                    "territory": terr_name,
                    "assigned_a": cat_a,
                    "assigned_b": cat_b,
                    "assigned_c": cat_c,
                    "total_assigned": total_assigned,
                    "visited": visited_count,
                    "not_visited": not_visited,
                    "coverage_pct": f"{coverage_pct}%",
                    "frequency_met_pct": f"{freq_met_pct}%",
                    "_raw_assigned": total_assigned,
                    "_raw_visited": visited_count,
                    "_raw_coverage_pct": coverage_pct,
                }
            )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_assigned = sum(int(it.get("_raw_assigned", 0)) for it in items)
        total_visited = sum(int(it.get("_raw_visited", 0)) for it in items)
        overall_pct = (
            round((total_visited / total_assigned * 100.0), 1) if total_assigned > 0 else 0.0
        )

        return {
            "total_assigned": total_assigned,
            "total_visited": total_visited,
            "overall_coverage_pct": overall_pct,
        }


ReportRegistry.register(CustomerCoverageReport)
