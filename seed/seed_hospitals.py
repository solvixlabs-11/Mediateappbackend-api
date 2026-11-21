"""Seeder for Hospitals (32 records across territories)."""

from sqlalchemy.orm import Session
from app.modules.customers.models import Hospital
from app.modules.territories.models import Territory
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="hospitals")
    territories = session.query(Territory).all()
    if not territories:
        return result

    hospitals_data = [
        ("Lilavati Hospital & Research Centre", "Multi-Specialty", 320, "Bandra West, Mumbai", "022-26751000"),
        ("Breach Candy Hospital Trust", "Super Specialty", 210, "Bhulabhai Desai Road, Mumbai", "022-23671888"),
        ("Hinduja Healthcare Surgical", "Super Specialty", 180, "Khar West, Mumbai", "022-30911000"),
        ("Kokilaben Dhirubhai Ambani Hospital", "Multi-Specialty", 750, "Four Bungalows, Andheri West, Mumbai", "022-30999999"),
        ("Ruby Hall Clinic", "Multi-Specialty", 550, "Sasoon Road, Pune", "020-66455100"),
        ("Apollo Hospitals", "Super Specialty", 500, "CBD Belapur, Navi Mumbai", "022-33503350"),
        ("Nanavati Max Super Specialty Hospital", "Multi-Specialty", 350, "SV Road, Vile Parle West, Mumbai", "022-26267500"),
        ("Jehangir Hospital", "Multi-Specialty", 350, "Bund Garden Road, Pune", "020-66811000"),
        ("Tata Memorial Centre Cancer Hospital", "Oncology Institute", 650, "Parel, Mumbai", "022-24177000"),
        ("Sir H.N. Reliance Foundation Hospital", "Multi-Specialty", 345, "Prarthana Samaj, Mumbai", "022-61305000"),
        ("Fortis Hospital Mulund", "Super Specialty", 315, "Mulund Goregaon Link Road, Mumbai", "022-67994444"),
        ("Jaslok Hospital & Research Centre", "Super Specialty", 364, "Pedder Road, Mumbai", "022-66573010"),
        ("Saifee Hospital", "Multi-Specialty", 257, "Charni Road, Mumbai", "022-67570111"),
        ("Bombay Hospital & Medical Research Centre", "Multi-Specialty", 830, "Marine Lines, Mumbai", "022-22067676"),
        ("KEM Hospital & Seth GS Medical College", "Government Medical College", 1800, "Parel, Mumbai", "022-24107000"),
        ("Deenanath Mangeshkar Hospital", "Multi-Specialty", 900, "Erandwane, Pune", "020-40151000"),
        ("Sahyadri Super Speciality Hospital", "Super Specialty", 220, "Deccan Gymkhana, Pune", "020-67213000"),
        ("Poona Hospital and Research Centre", "General Hospital", 300, "Sadashiv Peth, Pune", "020-24331707"),
        ("Zydus Hospital", "Super Specialty", 550, "SG Highway, Ahmedabad", "079-66190201"),
        ("Apollo CBCC Cancer Care", "Oncology Institute", 180, "Bhat, Gandhinagar", "079-66701800"),
        ("Sterling Hospitals", "Super Specialty", 300, "Memnagar, Ahmedabad", "079-40011111"),
        ("Kiran Multi Super Speciality Hospital", "Super Specialty", 850, "Katargam, Surat", "0261-7161111"),
        ("Manipal Hospital", "Multi-Specialty", 600, "Old Airport Road, Bengaluru", "080-25024444"),
        ("Narayana Health City", "Cardiac & Multi-Specialty", 1400, "Bommasandra, Bengaluru", "080-71222222"),
        ("Fortis Hospital Bannerghatta", "Super Specialty", 276, "Bannerghatta Road, Bengaluru", "080-66214444"),
        ("Aster CMI Hospital", "Multi-Specialty", 500, "Hebbal, Bengaluru", "080-43420100"),
        ("Max Super Speciality Hospital", "Super Specialty", 530, "Saket, New Delhi", "011-26515050"),
        ("Fortis Escorts Heart Institute", "Cardiac Institute", 310, "Okhla Road, New Delhi", "011-47135000"),
        ("Sir Ganga Ram Hospital", "Multi-Specialty", 675, "Rajinder Nagar, New Delhi", "011-25750000"),
        ("Indraprastha Apollo Hospitals", "Multi-Specialty", 710, "Sarita Vihar, New Delhi", "011-26925858"),
        ("Apollo Hospitals Greams Road", "Super Specialty", 600, "Greams Road, Chennai", "044-28290200"),
        ("Yashoda Hospitals", "Multi-Specialty", 700, "Somajiguda, Hyderabad", "040-45674567"),
    ]

    for i, (name, h_type, beds, addr, phone) in enumerate(hospitals_data, start=1):
        code = f"HOSP-{i:03d}"
        t = territories[(i - 1) % len(territories)]
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
                territory_id=t.id,
                is_active=True,
            )
            session.add(h)
            result.created += 1

    session.flush()
    return result
