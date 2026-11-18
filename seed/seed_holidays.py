"""Seeder for Holidays and Sunday weekly-offs."""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.modules.masters.models import MasterItem
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="holidays")

    # Generate major national holidays
    holidays = [
        ("2026-01-26", "Republic Day", "National Holiday"),
        ("2026-03-25", "Holi", "Gazetted Holiday"),
        ("2026-04-14", "Ambedkar Jayanti", "Gazetted Holiday"),
        ("2026-05-01", "Maharashtra Day / May Day", "State Holiday"),
        ("2026-08-15", "Independence Day", "National Holiday"),
        ("2026-10-02", "Gandhi Jayanti", "National Holiday"),
        ("2026-10-20", "Dussehra", "Gazetted Holiday"),
        ("2026-11-08", "Diwali", "Gazetted Holiday"),
        ("2026-12-25", "Christmas", "Gazetted Holiday"),
    ]

    for dt_str, name, desc in holidays:
        code = f"HOL-{dt_str}"
        existing = (
            session.query(MasterItem)
            .filter(MasterItem.type == "HOLIDAY", MasterItem.code == code)
            .first()
        )
        if existing:
            result.unchanged += 1
        else:
            item = MasterItem(
                type="HOLIDAY",
                code=code,
                name=f"{dt_str}: {name}",
                description=desc,
                sort_order=0,
                is_active=True,
            )
            session.add(item)
            result.created += 1

    session.flush()
    return result
