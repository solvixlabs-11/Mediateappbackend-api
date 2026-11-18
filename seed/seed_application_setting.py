"""Seeder for Application Setting (Company Profile)."""

import json
from sqlalchemy.orm import Session
from app.modules.masters.models import MasterItem
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="application_setting")
    data = load_json("application_setting.json")
    code = data.get("company_code", "MEDIATE").upper()
    existing = (
        session.query(MasterItem)
        .filter(MasterItem.type == "APPLICATION_SETTING", MasterItem.code == code)
        .first()
    )
    name = data.get("company_name", "Mediate Healthcare")
    desc = f"{data.get('area')}, {data.get('city')}, {data.get('state')} | Phone: {data.get('phone_no')}"[:250]
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
            type="APPLICATION_SETTING",
            code=code,
            name=name,
            description=desc,
            sort_order=1,
            is_active=True,
        )
        session.add(item)
        result.created += 1
    session.flush()
    return result
