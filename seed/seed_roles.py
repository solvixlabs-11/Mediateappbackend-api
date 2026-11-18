"""Seeder for Roles."""

from sqlalchemy.orm import Session
from app.modules.users.models import Role
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="roles")
    data = load_json("roles.json")
    for row in data:
        code = row["code"].upper()
        existing = session.query(Role).filter(Role.code == code).first()
        if existing:
            changed = False
            if existing.name != row["name"]:
                existing.name = row["name"]
                changed = True
            if existing.description != row.get("description"):
                existing.description = row.get("description")
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
            role = Role(
                code=code,
                name=row["name"],
                description=row.get("description"),
            )
            session.add(role)
            result.created += 1
    session.flush()
    return result
