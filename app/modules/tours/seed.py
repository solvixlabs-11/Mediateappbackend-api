"""Seed synthetic tour plan cutoff locks for dev environment."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.territories.models import Territory
from app.modules.tours.models import TourPlanLock
from app.modules.users.models import User


def seed_tour_plan_locks(db: Session) -> int:
    """Seed at least 12 synthetic tour plan locks."""
    existing_count = db.query(TourPlanLock).count()
    if existing_count >= 12:
        return existing_count

    admin = db.query(User).filter(User.email == "admin@mediate.com").first()
    if not admin:
        admin = db.query(User).first()
    if not admin:
        return 0

    territories = db.query(Territory).all()
    employees = db.query(User).all()

    current_year = datetime.now(UTC).year
    fin_year = f"{current_year}-{current_year+1}"
    seeded = 0

    # 1. Global ALL locks for past & future months
    for month in range(1, 13):
        # Determine cutoff date: 25th of preceding month
        cutoff = date(current_year, month, 25) if month <= 12 else date(current_year, 12, 25)
        status = "LOCKED" if month < 11 else ("UNLOCKED" if month == 11 else "LOCKED")
        reason = f"Monthly cutoff deadline lock for {date(current_year, month, 1).strftime('%B %Y')}"

        exists = (
            db.query(TourPlanLock)
            .filter(
                TourPlanLock.scope == "ALL",
                TourPlanLock.month == month,
                TourPlanLock.year == current_year,
            )
            .first()
        )
        if not exists:
            lock = TourPlanLock(
                scope="ALL",
                scope_id=None,
                month=month,
                year=current_year,
                financial_year=fin_year,
                cutoff_date=cutoff,
                status=status,
                reason=reason,
                created_by_id=admin.id,
                unlocked_by_id=admin.id if status == "UNLOCKED" else None,
                unlocked_at=datetime.now(UTC) if status == "UNLOCKED" else None,
            )
            db.add(lock)
            seeded += 1

    # 2. Territory-scoped locks
    if territories:
        for idx, terr in enumerate(territories[:3]):
            lock = TourPlanLock(
                scope="TERRITORY",
                scope_id=terr.id,
                month=12,
                year=current_year,
                financial_year=fin_year,
                cutoff_date=date(current_year, 11, 28),
                status="LOCKED" if idx == 0 else "UNLOCKED",
                reason=f"Territory operational route lock: {terr.name}",
                created_by_id=admin.id,
            )
            db.add(lock)
            seeded += 1

    # 3. Employee-scoped lock
    if employees:
        emp = employees[0]
        lock = TourPlanLock(
            scope="EMPLOYEE",
            scope_id=emp.id,
            month=12,
            year=current_year,
            financial_year=fin_year,
            cutoff_date=date(current_year, 11, 27),
            status="LOCKED",
            reason=f"Individual route lock for staff #{emp.id} ({emp.full_name})",
            created_by_id=admin.id,
        )
        db.add(lock)
        seeded += 1

    db.commit()
    return seeded


if __name__ == "__main__":
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        count = seed_tour_plan_locks(db)
        print(f"Seeded {count} tour plan cutoff locks.")
