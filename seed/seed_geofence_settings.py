"""Seeder for Geofence Settings."""

from sqlalchemy.orm import Session
from app.modules.settings.models import GeofenceSetting
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="geofence_settings")
    data = load_json("geofence_settings.json")
    for row in data:
        etype = row["entity_type"].upper()
        existing = session.query(GeofenceSetting).filter(GeofenceSetting.entity_type == etype).first()
        if existing:
            changed = False
            if existing.radius_m != row["radius_m"]:
                existing.radius_m = row["radius_m"]
                changed = True
            if existing.min_accuracy_m != row.get("min_accuracy_m", 50.0):
                existing.min_accuracy_m = row.get("min_accuracy_m", 50.0)
                changed = True
            if existing.is_provisional != row.get("is_provisional", False):
                existing.is_provisional = row.get("is_provisional", False)
                changed = True
            if changed:
                result.updated += 1
            else:
                result.unchanged += 1
        else:
            item = GeofenceSetting(
                entity_type=etype,
                radius_m=row["radius_m"],
                min_accuracy_m=row.get("min_accuracy_m", 50.0),
                is_provisional=row.get("is_provisional", False),
                is_active=True,
            )
            session.add(item)
            result.created += 1
    session.flush()
    return result
