"""Seeder for Territories."""

from sqlalchemy.orm import Session
from app.modules.masters.models import State
from app.modules.territories.models import Territory
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="territories")
    states = {s.code: s for s in session.query(State).all()}
    mh_id = states.get("MH", State(id=1)).id if states else 1
    gj_id = states.get("GJ", State(id=1)).id if states else 1
    ka_id = states.get("KA", State(id=1)).id if states else 1
    dl_id = states.get("DL", State(id=1)).id if states else 1

    territories_def = [
        ("T-MUM-01", "Mumbai Central & South", "Mumbai HQ", mh_id),
        ("T-MUM-02", "Mumbai Western Suburbs", "Andheri HQ", mh_id),
        ("T-MUM-03", "Mumbai Eastern Suburbs & Thane", "Thane HQ", mh_id),
        ("T-PUN-01", "Pune Urban Core", "Pune HQ", mh_id),
        ("T-PUN-02", "Pune PCMC & Industrial", "Pimpri HQ", mh_id),
        ("T-AMD-01", "Ahmedabad Metro", "Ahmedabad HQ", gj_id),
        ("T-SUR-01", "Surat & South Gujarat", "Surat HQ", gj_id),
        ("T-BLR-01", "Bengaluru Central & East", "Bengaluru HQ", ka_id),
        ("T-BLR-02", "Bengaluru South & West", "Jayanagar HQ", ka_id),
        ("T-DEL-01", "Delhi NCR Central", "Connaught Place HQ", dl_id),
    ]

    for code, name, hq, state_id in territories_def:
        existing = session.query(Territory).filter(Territory.code == code).first()
        if existing:
            changed = False
            if existing.name != name:
                existing.name = name
                changed = True
            if existing.headquarters != hq:
                existing.headquarters = hq
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
            t = Territory(
                code=code,
                name=name,
                headquarters=hq,
                state_id=state_id,
                is_active=True,
            )
            session.add(t)
            result.created += 1

    session.flush()
    return result
