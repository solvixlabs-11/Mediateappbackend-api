"""Seeder for Qualification Master."""

from sqlalchemy.orm import Session
from app.modules.masters.models import MasterItem
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="qualifications")
    data = load_json("qualifications.json")
    for row in data:
        code = row["code"].upper()
        existing = (
            session.query(MasterItem)
            .filter(MasterItem.type == "QUALIFICATION", MasterItem.code == code)
            .first()
        )
        if existing:
            changed = False
            if existing.name != row["name"]:
                existing.name = row["name"]
                changed = True
            if existing.description != row.get("description"):
                existing.description = row.get("description")
                changed = True
            if existing.sort_order != row.get("sort_order", 0):
                existing.sort_order = row.get("sort_order", 0)
                changed = True
            if existing.is_deleted:
                existing.is_deleted = False
                existing.is_active = True
                changed = True
            if changed:
                result.updated += 1
            else:
                result.unchanged += 1
        else:
            item = MasterItem(
                type="QUALIFICATION",
                code=code,
                name=row["name"],
                description=row.get("description"),
                sort_order=row.get("sort_order", 0),
                is_active=True,
            )
            session.add(item)
            result.created += 1
    session.flush()
    return result
