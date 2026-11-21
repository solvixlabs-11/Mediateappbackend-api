"""Seed Company Profile and Demo Meetings for Wave W6."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.modules.company_profile.service import CompanyProfileService
from app.modules.meetings.seed import seed_meetings


def main() -> None:
    db = SessionLocal()
    try:
        CompanyProfileService(db).get_profile()
        print("Company Profile verified / initialized.")
        seed_meetings(db)
        print("Demo Meetings seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
