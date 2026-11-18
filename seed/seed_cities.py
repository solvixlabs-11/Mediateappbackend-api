"""Seeder for Cities."""

from sqlalchemy.orm import Session
from app.modules.masters.models import City, State
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="cities")
    # State mapping
    states = {s.code: s for s in session.query(State).all()}
    if not states:
        return result

    mh = states.get("MH")
    gj = states.get("GJ")
    ka = states.get("KA")
    dl = states.get("DL")

    city_data = []
    if mh:
        city_data.extend([
            ("Mumbai", "MUM", mh.id),
            ("Pune", "PUN", mh.id),
            ("Nagpur", "NAG", mh.id),
            ("Nashik", "NSK", mh.id),
        ])
    if gj:
        city_data.extend([
            ("Ahmedabad", "AMD", gj.id),
            ("Surat", "SUR", gj.id),
            ("Vadodara", "BDQ", gj.id),
        ])
    if ka:
        city_data.extend([
            ("Bengaluru", "BLR", ka.id),
            ("Mysuru", "MYS", ka.id),
        ])
    if dl:
        city_data.extend([
            ("New Delhi", "DEL", dl.id),
        ])

    for name, code, state_id in city_data:
        existing = session.query(City).filter((City.name == name) | (City.code == code)).first()
        if existing:
            changed = False
            if existing.name != name:
                existing.name = name
                changed = True
            if existing.code != code:
                existing.code = code
                changed = True
            if existing.state_id != state_id:
                existing.state_id = state_id
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
            city = City(name=name, code=code, state_id=state_id, is_active=True)
            session.add(city)
            result.created += 1

    session.flush()
    return result
