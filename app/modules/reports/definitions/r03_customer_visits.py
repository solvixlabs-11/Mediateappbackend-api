"""R03 - Customer-wise Visits Report."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.customers.models import Chemist, Doctor
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema


class CustomerVisitsReport(BaseReport):
    """R03 Customer-wise Visits.

    Per doctor/chemist/stockist/hospital: total visits, last visit, days since, next due.
    """

    key = "customer_visits"
    title = "Customer-wise Visits Report"
    group = "Customers"
    description = "Per doctor/chemist/stockist/hospital: total visits in range, last visit, days since, and compliance status."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
        customer_type_picker=True,
        status_picker=True,
        status_options=["All", "On track", "Due", "Overdue"],
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="customer_name", label="Customer", type="string"),
            ReportColumn(key="customer_type", label="Type", type="string"),
            ReportColumn(key="category", label="Category", type="string", align="center"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="total_visits", label="Visits in Range", type="number", align="right"),
            ReportColumn(
                key="last_visit_date", label="Last Visit Date", type="date", align="center"
            ),
            ReportColumn(
                key="days_since_last_visit", label="Days Since", type="number", align="right"
            ),
            ReportColumn(key="next_visit_due", label="Next Due", type="date", align="center"),
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
        today = date.today()
        results: list[dict[str, Any]] = []

        # Query all doctors
        doc_stmt = (
            select(Doctor).options(selectinload(Doctor.territory)).where(Doctor.is_active.is_(True))
        )
        if filters.territory_id:
            doc_stmt = doc_stmt.where(Doctor.territory_id == filters.territory_id)
        doctors = db.scalars(doc_stmt).all()

        for d in doctors:
            # Visits in range
            v_stmt = select(func.count(DcrVisit.id), func.max(DcrVisit.dcr_date)).where(
                DcrVisit.doctor_id == d.id,
            )
            if user_ids is not None:
                v_stmt = v_stmt.where(DcrVisit.user_id.in_(user_ids))
            if start_utc and end_utc:
                v_stmt = v_stmt.where(
                    DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc
                )

            v_count, last_dt = db.execute(v_stmt).first() or (0, None)
            visits_in_range = int(v_count or 0)

            days_since = (today - last_dt).days if last_dt else 999

            # Status logic based on visit frequency
            if not last_dt:
                status_str = "Overdue"
            elif days_since <= 15:
                status_str = "On track"
            elif days_since <= 30:
                status_str = "Due"
            else:
                status_str = "Overdue"

            if filters.status and filters.status.lower() != "all":
                if status_str.lower() != filters.status.lower():
                    continue

            results.append(
                {
                    "customer_name": f"Dr. {d.full_name}",
                    "customer_type": "Doctor",
                    "category": d.category or "A",
                    "territory": d.territory.name if d.territory else "-",
                    "mr_name": "Assigned MR",
                    "total_visits": visits_in_range,
                    "last_visit_date": last_dt.isoformat() if last_dt else "Never",
                    "days_since_last_visit": days_since if last_dt else None,
                    "next_visit_due": "-",
                    "status": status_str,
                    "_raw_status": status_str,
                    "_raw_visited": visits_in_range > 0,
                }
            )

        # Similarly add chemists if customer_type allows
        if not filters.customer_type or filters.customer_type.upper() in ["ALL", "CHEMIST"]:
            chem_stmt = (
                select(Chemist)
                .options(selectinload(Chemist.territory))
                .where(Chemist.is_active.is_(True))
            )
            if filters.territory_id:
                chem_stmt = chem_stmt.where(Chemist.territory_id == filters.territory_id)
            chemists = db.scalars(chem_stmt).all()
            for c in chemists:
                cv_stmt = select(func.count(DcrVisit.id), func.max(DcrVisit.dcr_date)).where(
                    DcrVisit.chemist_id == c.id,
                )
                if user_ids is not None:
                    cv_stmt = cv_stmt.where(DcrVisit.user_id.in_(user_ids))
                if start_utc and end_utc:
                    cv_stmt = cv_stmt.where(
                        DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc
                    )

                cv_count, c_last = db.execute(cv_stmt).first() or (0, None)
                c_visits = int(cv_count or 0)
                c_days = (today - c_last).days if c_last else 999
                c_stat = "On track" if c_days <= 20 else ("Due" if c_days <= 35 else "Overdue")

                if filters.status and filters.status.lower() != "all":
                    if c_stat.lower() != filters.status.lower():
                        continue

                results.append(
                    {
                        "customer_name": c.shop_name,
                        "customer_type": "Chemist",
                        "category": "Retailer",
                        "territory": c.territory.name if c.territory else "-",
                        "mr_name": "Assigned MR",
                        "total_visits": c_visits,
                        "last_visit_date": c_last.isoformat() if c_last else "Never",
                        "days_since_last_visit": c_days if c_last else None,
                        "next_visit_due": "-",
                        "status": c_stat,
                        "_raw_status": c_stat,
                        "_raw_visited": c_visits > 0,
                    }
                )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_customers = len(items)
        if total_customers == 0:
            return {
                "customers": 0,
                "never_visited": 0,
                "overdue": 0,
                "on_track": 0,
            }

        never_visited = sum(1 for it in items if it.get("last_visit_date") == "Never")
        overdue = sum(1 for it in items if it.get("_raw_status") == "Overdue")
        on_track = sum(1 for it in items if it.get("_raw_status") == "On track")

        return {
            "customers": total_customers,
            "never_visited": never_visited,
            "overdue": overdue,
            "on_track": on_track,
        }


ReportRegistry.register(CustomerVisitsReport)
