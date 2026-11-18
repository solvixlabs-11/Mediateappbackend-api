"""Seeder for Tour Programs."""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.modules.tours.models import TourProgram
from app.modules.users.models import User
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="tour_plans")
    if not dev:
        return result

    users = session.query(User).filter(User.is_active == True).limit(5).all()  # noqa: E712
    today = date.today()
    start_date = today.replace(day=1)
    end_date = start_date + timedelta(days=27)

    for u in users:
        existing = (
            session.query(TourProgram)
            .filter(
                TourProgram.user_id == u.id,
                TourProgram.start_date == start_date,
            )
            .first()
        )
        if not existing:
            tp = TourProgram(
                user_id=u.id,
                title=f"Monthly Field Plan - {today.strftime('%B %Y')}",
                start_date=start_date,
                end_date=end_date,
                total_days=24,
                route_details="Metro Territory Coverage & Key Doctor Detailing",
                objectives="Achieve 95%+ coverage on Super-Core and Core doctors, boost POB conversions",
                status="SUBMITTED",
            )
            session.add(tp)
            result.created += 1
        else:
            result.unchanged += 1

    session.flush()
    return result
