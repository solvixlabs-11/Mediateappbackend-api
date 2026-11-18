"""Idempotent seed script for Masters - Part 1.

Usage:
    python scripts/seed_masters.py
"""

import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.modules.masters.seed import seed_masters

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_seed() -> None:
    """Run idempotent masters seeding."""
    logger.info("Starting idempotent masters seeding...")
    db = SessionLocal()
    try:
        seed_masters(db)
        logger.info("Masters seeding completed successfully.")
    except Exception as exc:
        logger.exception("Masters seeding failed: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
