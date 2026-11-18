"""Seeder for Hospitals."""

from sqlalchemy.orm import Session
from app.modules.customers.models import Hospital
from app.modules.territories.models import Territory
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="hospitals")
    territory = session.query(Territory).first()
    t_id = territory.id if territory else 1

    hospitals_data = [
        ("Lilavati Hospital & Research Centre", "Multi-Specialty", 320, "Bandra West, Mumbai", "022-26751000"),
        ("Breach Candy Hospital Trust", "Super Specialty", 210, "Bhulabhai Desai Road, Mumbai", "022-23671888"),
        ("Hinduja Healthcare Surgical", "Super Specialty", 180, "Khar West, Mumbai", "022-30911000"),
        ("Kokilaben Dhirubhai Ambani Hospital", "Multi-Specialty", 750, "Four Bungalows, Andheri West, Mumbai", "022-30999999"),
        ("Ruby Hall Clinic", "Multi-Specialty", 550, "Sasoon Road, Pune", "020-66455100"),
        ("Apollo Hospitals", "Super Specialty", 500, "CBD Belapur, Navi Mumbai", "022-33503350"),
        ("Nanavati Max Super Specialty Hospital", "Multi-Specialty", 350, "SV Road, Vile Parle West, Mumbai", "022-26267500"),
        ("Jehangir Hospital", "Multi-Specialty", 350, "Bund Garden Road, Pune", "020-66811000"),
    ]

    for i, (name, h_type, beds, addr, phone) in enumerate(hospitals_data, start=1):
        code = f"HOSP-{i:03d}"
        existing = session.query(Hospital).filter((Hospital.code == code) | (Hospital.name == name)).first()
        if existing:
            changed = False
            if existing.bed_count != beds:
                existing.bed_count = beds
                changed = True
            if existing.type != h_type:
                existing.type = h_type
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
            h = Hospital(
                name=name,
                code=code,
                type=h_type,
                bed_count=beds,
                address=addr,
                phone=phone,
                territory_id=t_id,
                is_active=True,
            )
            session.add(h)
            result.created += 1

    session.flush()
    return result
