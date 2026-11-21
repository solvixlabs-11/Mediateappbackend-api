"""Seeder for App Releases / What's New."""

from sqlalchemy.orm import Session
from app.modules.releases.seed import seed_app_releases
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="app_releases")
    seed_app_releases(session)
    result.created += 3
    return result
