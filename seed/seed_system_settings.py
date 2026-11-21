"""Seeder for System Configuration Settings."""

from sqlalchemy.orm import Session
from app.modules.settings.models import AppSetting
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="system_settings")
    data = load_json("system_settings.json")
    for row in data:
        key = row["key"]
        existing = session.query(AppSetting).filter(AppSetting.key == key).first()
        if existing:
            changed = False
            if existing.group != row["group"]:
                existing.group = row["group"]
                changed = True
            if existing.value_type != row["value_type"]:
                existing.value_type = row["value_type"]
                changed = True
            if existing.unit != row.get("unit"):
                existing.unit = row.get("unit")
                changed = True
            if existing.min_value != row.get("min_value"):
                existing.min_value = row.get("min_value")
                changed = True
            if existing.max_value != row.get("max_value"):
                existing.max_value = row.get("max_value")
                changed = True
            if existing.allowed_options != row.get("allowed_options"):
                existing.allowed_options = row.get("allowed_options")
                changed = True
            if existing.help_text != row.get("help_text"):
                existing.help_text = row.get("help_text")
                changed = True
            if existing.is_provisional != row.get("is_provisional", False):
                existing.is_provisional = row.get("is_provisional", False)
                changed = True
            if changed:
                result.updated += 1
            else:
                result.unchanged += 1
        else:
            item = AppSetting(
                key=key,
                group=row["group"],
                value=str(row["value"]),
                value_type=row["value_type"],
                unit=row.get("unit"),
                min_value=row.get("min_value"),
                max_value=row.get("max_value"),
                allowed_options=row.get("allowed_options"),
                help_text=row.get("help_text"),
                is_provisional=row.get("is_provisional", False),
                is_active=True,
            )
            session.add(item)
            result.created += 1
    session.flush()
    return result
