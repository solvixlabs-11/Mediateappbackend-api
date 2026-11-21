"""Seeder for Doctors (32 records across specialties)."""

from sqlalchemy.orm import Session
from app.modules.customers.models import Doctor
from app.modules.territories.models import Territory
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="doctors")
    territories = session.query(Territory).all()
    if not territories:
        return result

    sample_doctors = [
        ("DOC001", "Dr. Rajesh K. Sharma", "Cardiology", "MD, DM", "A+"),
        ("DOC002", "Dr. Ananya P. Desai", "Diabetology", "MBBS, MD", "A"),
        ("DOC003", "Dr. Vikramaditya Joshi", "General Medicine", "MBBS, MD", "A"),
        ("DOC004", "Dr. Sneha S. Kulkarni", "Pediatrics", "MBBS, DCH, DNB", "B"),
        ("DOC005", "Dr. Arvind M. Mehta", "Orthopedics", "MS, DNB", "A"),
        ("DOC006", "Dr. Meenakshi S. Sundaram", "Gynecology", "MD, DGO", "A+"),
        ("DOC007", "Dr. Prateek B. Kapoor", "Dermatology", "MD, DVD", "B"),
        ("DOC008", "Dr. Farhan N. Merchant", "Oncology", "MD, DM", "A+"),
        ("DOC009", "Dr. Kavita H. Saxena", "Neurology", "MD, DM", "A"),
        ("DOC010", "Dr. Rohit T. Agarwal", "Gastroenterology", "MD, DNB", "A"),
        ("DOC011", "Dr. Harish C. Pillai", "Nephrology", "MD, DM", "A+"),
        ("DOC012", "Dr. Deepa V. Nambiar", "Endocrinology", "MBBS, MD", "A"),
        ("DOC013", "Dr. Sunil R. Bhosale", "Pulmonology", "MD, DTCD", "B"),
        ("DOC014", "Dr. Priyanka G. Sen", "Psychiatry", "MD, DPM", "B"),
        ("DOC015", "Dr. Anand K. Rao", "Ophthalmology", "MS, DO", "B"),
        ("DOC016", "Dr. Smita R. Chavan", "ENT", "MS (ENT)", "B"),
        ("DOC017", "Dr. Chetan M. Shah", "Urology", "MS, MCh", "A+"),
        ("DOC018", "Dr. Bhavana D. Jadhav", "Rheumatology", "MD, DM", "A"),
        ("DOC019", "Dr. Alok V. Dubey", "General Surgery", "MS", "B"),
        ("DOC020", "Dr. Archana S. Shinde", "Pathology", "MD", "C"),
        ("DOC021", "Dr. Vinod P. Pandey", "General Medicine", "MBBS", "C"),
        ("DOC022", "Dr. Swati M. Kadam", "Obstetrics & Gynae", "MBBS, DGO", "B"),
        ("DOC023", "Dr. Nikhil S. Chopra", "Cardiology", "MD, DM", "A+"),
        ("DOC024", "Dr. Radhika N. Hegde", "Dermatology", "MD", "B"),
        ("DOC025", "Dr. Gaurav T. Namboodiri", "Pediatrics", "MD", "A"),
        ("DOC026", "Dr. Shweta K. More", "Diabetology", "MBBS, Dip. Diab.", "B"),
        ("DOC027", "Dr. Manish R. Gupta", "Orthopedics", "MS", "A"),
        ("DOC028", "Dr. Preeti S. Verma", "General Medicine", "MD", "B"),
        ("DOC029", "Dr. Arun K. Nair", "Chest Physician", "MD", "B"),
        ("DOC030", "Dr. Pallavi S. Joshi", "Pediatrics", "MBBS, DNB", "B"),
        ("DOC031", "Dr. Kiran V. Patel (Field Reg)", "Cardiology", "MD, DM", "A"),
        ("DOC032", "Dr. Tushar B. Deshmukh (Field Reg)", "Diabetology", "MBBS, MD", "B"),
    ]

    for idx, (code, name, spec, qual, cat) in enumerate(sample_doctors):
        t = territories[idx % len(territories)]
        existing = session.query(Doctor).filter(Doctor.code == code).first()
        is_pending = idx >= 28  # Last 4 pending for field approval inbox testing

        if existing:
            changed = False
            if existing.full_name != name:
                existing.full_name = name
                changed = True
            if existing.specialization != spec:
                existing.specialization = spec
                changed = True
            if existing.qualification != qual:
                existing.qualification = qual
                changed = True
            if existing.is_deleted:
                existing.is_deleted = False
                changed = True
            if existing.is_active != (not is_pending):
                existing.is_active = not is_pending
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
                is_active=not is_pending,
            )
            session.add(doc)
            result.created += 1

    session.flush()
    return result
