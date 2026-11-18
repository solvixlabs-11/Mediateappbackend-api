"""Seeder for Doctors."""

from sqlalchemy.orm import Session
from app.modules.customers.models import Doctor
from app.modules.territories.models import Territory
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="doctors")
    territories = session.query(Territory).all()
    if not territories:
        return result

    specs = ["Cardiology", "Pediatrics", "Dermatology", "General Medicine", "Orthopedics", "Gynecology & Obstetrics"]
    quals = ["MBBS, MD", "MBBS, MS", "MBBS, DGO", "MD (Medicine)", "DNB", "MBBS"]

    sample_doctors = [
        ("DOC001", "Dr. Rajesh Sharma", "Cardiology", "MBBS, MD", "SUPER_CORE"),
        ("DOC002", "Dr. Priya Deshmukh", "Gynecology & Obstetrics", "MBBS, DGO", "CORE"),
        ("DOC003", "Dr. Vikram Malhotra", "Orthopedics", "MBBS, MS", "CORE"),
        ("DOC004", "Dr. Ananya Iyer", "Pediatrics", "MBBS, DNB", "GENERAL"),
        ("DOC005", "Dr. Suresh Joshi", "General Medicine", "MD (Medicine)", "POTENTIAL"),
        ("DOC006", "Dr. Meera Nambiar", "Dermatology", "MBBS, DDVL", "CORE"),
        ("DOC007", "Dr. Amit Patel", "Diabetology", "MBBS, MD", "SUPER_CORE"),
        ("DOC008", "Dr. Sunita Kulkarni", "Ophthalmology", "MS (Ophthal)", "GENERAL"),
        ("DOC009", "Dr. Rohan Mehta", "ENT", "MBBS, MS (ENT)", "POTENTIAL"),
        ("DOC010", "Dr. Pooja Verma", "General Medicine", "MBBS", "CORE"),
    ]

    for idx, (code, name, spec, qual, cat) in enumerate(sample_doctors):
        t = territories[idx % len(territories)]
        existing = session.query(Doctor).filter(Doctor.code == code).first()
        if existing:
            changed = False
            if existing.full_name != name:
                existing.full_name = name
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
            doc = Doctor(
                code=code,
                full_name=name,
                specialization=spec,
                qualification=qual,
                category=cat,
                territory_id=t.id,
                phone=f"+9198200{10000 + idx}",
                address=f"Clinic Suite {101 + idx}, Health Centre, {t.name}",
                is_active=True,
            )
            session.add(doc)
            result.created += 1

    session.flush()
    return result
