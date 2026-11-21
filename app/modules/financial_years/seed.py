"""Seed script for corporate Financial Years."""

from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.financial_years.models import FinancialYear


def seed_financial_years(db: Session):
    default_fys = [
        {
            "name": "FY 2024-2025",
            "code": "2024-2025",
            "start_date": date(2024, 4, 1),
            "end_date": date(2025, 3, 31),
            "is_current": False,
            "is_active": True,
            "description": "Previous audited corporate financial year",
        },
        {
            "name": "FY 2025-2026",
            "code": "2025-2026",
            "start_date": date(2025, 4, 1),
            "end_date": date(2026, 3, 31),
            "is_current": True,
            "is_active": True,
            "description": "Current active operating financial year",
        },
        {
            "name": "FY 2026-2027",
            "code": "2026-2027",
            "start_date": date(2026, 4, 1),
            "end_date": date(2027, 3, 31),
            "is_current": False,
            "is_active": True,
            "description": "Upcoming business plan and annual budget financial year",
        },
    ]

    for item in default_fys:
        stmt = select(FinancialYear).where(FinancialYear.code == item["code"])
        existing = db.scalar(stmt)
        if not existing:
            fy = FinancialYear(**item)
            db.add(fy)
    db.commit()
    print("[SEED] Financial years seeded successfully.")
