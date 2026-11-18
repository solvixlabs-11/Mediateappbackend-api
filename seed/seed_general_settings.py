"""Seeder for General Settings."""

from sqlalchemy.orm import Session
from app.modules.masters.models import MasterItem
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="general_settings")
    data = load_json("general_settings.json")
    for row in data:
        code = row["key"]
        existing = (
            session.query(MasterItem)
            .filter(MasterItem.type == "GENERAL_SETTING", MasterItem.code == code)
            .first()
        )
        # Store as: name = module, description = question | answer
        name = row["module"]
        desc = f"{row['question']} -> {row['value']} ({row['value_type']})"
        if existing:
            changed = False
            if existing.name != name:
                existing.name = name
                changed = True
            if existing.description != desc:
                existing.description = desc
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
                type="GENERAL_SETTING",
                code=code,
                name=name,
                description=desc,
                sort_order=row.get("sort_order", 0),
                is_active=True,
            )
            session.add(item)
            result.created += 1
    session.flush()
    return result
