"""Seeder for Report Definitions (Catalog v3 - 48 reports)."""

from sqlalchemy.orm import Session
from app.db.base import Base
from app.modules.reports.models import ReportDefinition
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="report_definitions")

    # Ensure table exists in database
    bind = session.get_bind()
    ReportDefinition.__table__.create(bind, checkfirst=True)

    items = load_json("report_definitions.json")

    for d in items:
        key = d["key"]
        existing = session.query(ReportDefinition).filter(ReportDefinition.key == key).first()

        if existing:
            changed = False
            if existing.name != d["name"]:
                existing.name = d["name"]
                changed = True
            if existing.group != d["group"]:
                existing.group = d["group"]
                changed = True
            if existing.description != d.get("description"):
                existing.description = d.get("description")
                changed = True
            if existing.sort_order != d.get("sort_order", 0):
                existing.sort_order = d.get("sort_order", 0)
                changed = True
            if existing.status != d.get("status", "AVAILABLE"):
                existing.status = d.get("status", "AVAILABLE")
                changed = True
            if existing.unavailable_reason != d.get("unavailable_reason"):
                existing.unavailable_reason = d.get("unavailable_reason")
                changed = True
            if existing.formats != d.get("formats", []):
                existing.formats = d.get("formats", [])
                changed = True
            if existing.filter_schema != d.get("filter_schema", {}):
                existing.filter_schema = d.get("filter_schema", {})
                changed = True
            if existing.allowed_roles != d.get("allowed_roles", []):
                existing.allowed_roles = d.get("allowed_roles", [])
                changed = True
            if existing.data_as_of_source != d.get("data_as_of_source"):
                existing.data_as_of_source = d.get("data_as_of_source")
                changed = True

            if changed:
                result.updated += 1
            else:
                result.unchanged += 1
        else:
            rep = ReportDefinition(
                key=key,
                name=d["name"],
                group=d["group"],
                description=d.get("description"),
                sort_order=d.get("sort_order", 0),
                status=d.get("status", "AVAILABLE"),
                unavailable_reason=d.get("unavailable_reason"),
                formats=d.get("formats", []),
                filter_schema=d.get("filter_schema", {}),
                allowed_roles=d.get("allowed_roles", []),
                data_as_of_source=d.get("data_as_of_source"),
                is_active=True,
            )
            session.add(rep)
            result.created += 1

    session.flush()
    return result
