"""Seeder for Financial Year Master."""

from sqlalchemy.orm import Session
from app.modules.masters.models import MasterItem
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="financial_years")
    fys = [
        ("2425", "2024-2025", "01/04/2024 to 31/03/2025", 1),
        ("2526", "2025-2026", "01/04/2025 to 31/03/2026", 2),
        ("2627", "2026-2027", "01/04/2026 to 31/03/2027", 3),
    ]
    for code, name, desc, sort in fys:
        existing = (
            session.query(MasterItem)
            .filter(MasterItem.type == "FINANCIAL_YEAR", MasterItem.code == code)
            .first()
        )
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
                type="FINANCIAL_YEAR",
                code=code,
                name=name,
                description=desc,
                sort_order=sort,
                is_active=True,
            )
            session.add(item)
            result.created += 1
    session.flush()
    return result
