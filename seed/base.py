"""Base utilities for modular database seeders."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

DATA_DIR = Path(__file__).resolve().parent / "data"


@dataclass
class SeedResult:
    """Standard seeder return object reporting mutation counts."""

    name: str
    created: int = 0
    updated: int = 0
    unchanged: int = 0

    @property
    def total(self) -> int:
        return self.created + self.updated + self.unchanged

    def __str__(self) -> str:
        return (
            f"[{self.name}] Total: {self.total} | "
            f"Created: {self.created} | Updated: {self.updated} | Unchanged: {self.unchanged}"
        )


def load_json(filename: str) -> Any:
    """Load JSON file from seed/data/ directory."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Seed data file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
