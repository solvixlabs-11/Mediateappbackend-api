"""Unassigned_Customers_Division_Wise_Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Chemist, Doctor
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn


class UnassignedCustomersDivisionReport(BaseReport):
    key = "unassigned_customers_division"
    title = "Unassigned_Customers_Division_Wise_Report"
    group = "Doctor & Customer"
    description = "Customers with no employee assigned, by division."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="customer_type", label="Customer Type", type="string", align="center"),
            ReportColumn(key="name", label="Customer Name", type="string"),
            ReportColumn(key="division", label="Division", type="string"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        docs = db.execute(select(Doctor).where(Doctor.territory_id.is_(None))).scalars().all()
        chms = db.execute(select(Chemist).where(Chemist.territory_id.is_(None))).scalars().all()
        rows = []
        for d in docs:
            rows.append({
                "customer_type": "DOCTOR",
                "name": d.full_name,
                "division": "MEDIATE",
                "status": "UNASSIGNED",
            })
        for c in chms:
            rows.append({
                "customer_type": "CHEMIST",
                "name": c.shop_name,
                "division": "MEDIATE",
                "status": "UNASSIGNED",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_unassigned_customers": len(items),
        }

ReportEngineRegistry.register(UnassignedCustomersDivisionReport)
