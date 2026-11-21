"""Seeder for Financial Year Master."""

from datetime import date
from sqlalchemy.orm import Session
from app.modules.masters.models import MasterItem
from app.modules.financial_years.models import FinancialYear
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

    # Also seed dedicated financial_years table
    dedicated_fys = [
        {
            "name": "FY 2024-2025",
            "code": "2024-2025",
            "start_date": date(2024, 4, 1),
            "end_date": date(2025, 3, 31),
            "is_current": False,
            "is_active": True,
            "description": "01/04/2024 to 31/03/2025",
        },
        {
            "name": "FY 2025-2026",
            "code": "2025-2026",
            "start_date": date(2025, 4, 1),
            "end_date": date(2026, 3, 31),
            "is_current": True,
            "is_active": True,
            "description": "01/04/2025 to 31/03/2026 (Active Fiscal Operating Year)",
        },
        {
            "name": "FY 2026-2027",
            "code": "2026-2027",
            "start_date": date(2026, 4, 1),
            "end_date": date(2027, 3, 31),
            "is_current": False,
            "is_active": True,
            "description": "01/04/2026 to 31/03/2027 (Upcoming Annual Budget Year)",
        },
    ]

    for dfy in dedicated_fys:
        fy_row = session.query(FinancialYear).filter(FinancialYear.code == dfy["code"]).first()
        if not fy_row:
            fy_row = FinancialYear(**dfy)
            session.add(fy_row)

    session.flush()
    return result
