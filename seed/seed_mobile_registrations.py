"""Dev seeder for synthetic mobile registrations."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from app.modules.mobile_registrations.seed import seed_mobile_registrations
from seed.base import SeedResult


def run(session: Session, **kwargs: Any) -> SeedResult:
    result = SeedResult(name="mobile_registrations")
    count = seed_mobile_registrations(session)
    result.created = count
    return result
