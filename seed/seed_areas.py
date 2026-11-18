"""Seeder for Areas."""

from sqlalchemy.orm import Session
from app.modules.masters.models import Area, City
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="areas")
    cities = {c.name: c for c in session.query(City).all()}
    if not cities:
        return result

    area_data = []
    if "Mumbai" in cities:
        m_id = cities["Mumbai"].id
        area_data.extend([
            ("Andheri West", "400053", m_id),
            ("Bandra West", "400050", m_id),
            ("Borivali West", "400092", m_id),
            ("Dadar", "400014", m_id),
            ("Ghatkopar East", "400077", m_id),
            ("Colaba", "400005", m_id),
            ("Powai", "400076", m_id),
            ("Malad West", "400064", m_id),
        ])
    if "Pune" in cities:
        p_id = cities["Pune"].id
        area_data.extend([
            ("Kothrud", "411038", p_id),
            ("Shivajinagar", "411005", p_id),
            ("Hinjewadi", "411057", p_id),
            ("Viman Nagar", "411014", p_id),
        ])
    if "Ahmedabad" in cities:
        a_id = cities["Ahmedabad"].id
        area_data.extend([
            ("Navrangpura", "380009", a_id),
            ("Satellite", "380015", a_id),
            ("Bodakdev", "380054", a_id),
        ])
    if "Bengaluru" in cities:
        b_id = cities["Bengaluru"].id
        area_data.extend([
            ("Koramangala", "560034", b_id),
            ("Indiranagar", "560038", b_id),
            ("Whitefield", "560066", b_id),
        ])

    for name, pincode, city_id in area_data:
        existing = session.query(Area).filter(Area.name == name).first()
        if existing:
            changed = False
            if existing.city_id != city_id:
                existing.city_id = city_id
                changed = True
            if existing.pincode != pincode:
                existing.pincode = pincode
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
            area = Area(name=name, pincode=pincode, city_id=city_id, is_active=True)
            session.add(area)
            result.created += 1

    session.flush()
    return result
