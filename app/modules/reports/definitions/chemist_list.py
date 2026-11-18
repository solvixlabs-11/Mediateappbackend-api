"""Chemist List Master Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customers.models import Chemist
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.territories.models import Territory


class ChemistListReport(BaseReport):
    key = "chemist_list"
    title = "Chemist List"
    group = "Doctor & Customer"
    description = "Chemist master listing with drug license, phone, and territory info."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="code", label="Chemist Code", type="string", align="center"),
            ReportColumn(key="shop_name", label="Pharmacy / Shop Name", type="string"),
            ReportColumn(key="contact", label="Contact Person", type="string"),
            ReportColumn(key="dl_number", label="DL Number", type="string"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="phone", label="Phone", type="string"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        chemists = db.execute(select(Chemist)).scalars().all()
        t_cache = {t.id: t.name for t in db.execute(select(Territory)).scalars().all()}
        rows = []
        for c in chemists:
            rows.append({
                "code": c.code,
                "shop_name": c.shop_name,
                "contact": c.contact_person or "-",
                "dl_number": c.dl_number or "-",
                "territory": t_cache.get(c.territory_id, "Central"),
                "phone": c.phone or "-",
                "status": "ACTIVE" if c.is_active else "INACTIVE",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_chemists": len(items),
            "active_chemists": sum(1 for i in items if i.get("status") == "ACTIVE"),
        }

ReportEngineRegistry.register(ChemistListReport)
