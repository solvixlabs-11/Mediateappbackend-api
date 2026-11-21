"""Dev seeder for synthetic tour plan locks."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from app.modules.tours.seed import seed_tour_plan_locks
from seed.base import SeedResult


def run(session: Session, **kwargs: Any) -> SeedResult:
    result = SeedResult(name="tour_plan_locks")
    count = seed_tour_plan_locks(session)
    result.created = count
    return result
