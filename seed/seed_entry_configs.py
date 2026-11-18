"""Seeder for Entry-wise Configurations."""

from sqlalchemy.orm import Session
from app.modules.masters.models import MasterItem
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="entry_configs")
    data = load_json("entry_configs.json")
    for idx, row in enumerate(data, 1):
        code = row["entry_key"].upper()
        existing = (
            session.query(MasterItem)
            .filter(MasterItem.type == "ENTRY_CONFIG", MasterItem.code == code)
            .first()
        )
        name = row["label"]
        desc = row["transaction_type"]
        if existing:
            changed = False
            if existing.name != name:
                existing.name = name
                changed = True
            if existing.description != desc:
                existing.description = desc
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
                type="ENTRY_CONFIG",
                code=code,
                name=name,
                description=desc,
                sort_order=idx,
                is_active=True,
            )
            session.add(item)
            result.created += 1
    session.flush()
    return result
