"""Territory Hierarchy Report."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.territories.models import Territory
from app.modules.users.models import User


class TerritoryHierarchyReport(BaseReport):
    key = "territory_hierarchy_report"
    title = "Territory Hierarchy Report"
    group = "Doctor & Customer"
    description = "Territory tree with employees and designations."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="territory", label="Territory Name", type="string"),
            ReportColumn(key="code", label="Territory Code", type="string", align="center"),
            ReportColumn(key="assigned_emp", label="Assigned Rep", type="string"),
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        territories = db.execute(select(Territory)).scalars().all()
        user_cache = {u.territory_id: u for u in db.execute(select(User).where(User.territory_id.isnot(None))).scalars().all()}
        rows = []
        for t in territories:
            u = user_cache.get(t.id)
            rows.append({
                "territory": t.name,
                "code": t.code,
                "assigned_emp": u.full_name if u else "Unassigned",
                "designation": getattr(u, "designation", "MR") if u else "-",
                "status": "ACTIVE" if t.is_active else "INACTIVE",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_territories": len(items),
            "assigned_territories": sum(1 for i in items if i.get("assigned_emp") != "Unassigned"),
        }

ReportEngineRegistry.register(TerritoryHierarchyReport)
