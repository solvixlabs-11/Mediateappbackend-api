"""Seeder for States."""

from sqlalchemy.orm import Session
from app.modules.masters.models import State
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="states")
    data = load_json("states.json")
    for row in data:
        code = row["code"].upper()
        name = row["name"]
        existing = (
            session.query(State)
            .filter((State.code == code) | (State.name == name))
            .first()
        )
        if existing:
            changed = False
            if existing.name != name:
                existing.name = name
                changed = True
            if existing.code != code:
                # only update code if code doesn't conflict
                code_conflict = session.query(State).filter(State.code == code, State.id != existing.id).first()
                if not code_conflict:
                    existing.code = code
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
            state = State(name=row["name"], code=code, is_active=True)
            session.add(state)
            result.created += 1
    session.flush()
    return result
