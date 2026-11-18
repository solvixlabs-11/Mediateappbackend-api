"""Seeder for Chemists."""

from sqlalchemy.orm import Session
from app.modules.customers.models import Chemist
from app.modules.territories.models import Territory
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="chemists")
    territories = session.query(Territory).all()
    if not territories:
        return result

    sample_chemists = [
        ("CHM001", "Sanjivani Medical Store", "Ramesh Shah", "20B-MH-102938"),
        ("CHM002", "Apollo Pharmacy Bandra", "Suresh Nair", "20B-MH-102939"),
        ("CHM003", "Wellness Forever Chemists", "Kiran Patel", "20B-MH-102940"),
        ("CHM004", "Noble Chemists & Druggists", "Ashok Jain", "20B-MH-102941"),
        ("CHM005", "Dhanvantari Medico", "Pravin Kulkarni", "20B-MH-102942"),
        ("CHM006", "MedPlus Pharmacy Pune", "Mahesh Shinde", "20B-MH-102943"),
        ("CHM007", "Shree Ganesh Medicals", "Ganesh Jadhav", "20B-MH-102944"),
        ("CHM008", "LifeCare Chemist Andheri", "Vipul Parekh", "20B-MH-102945"),
        ("CHM009", "National Medical Store", "Abdul Razzak", "20B-MH-102946"),
        ("CHM010", "Trust Pharmacy Colaba", "Farhan Merchant", "20B-MH-102947"),
    ]

    for idx, (code, shop_name, contact, dl_no) in enumerate(sample_chemists):
        t = territories[idx % len(territories)]
        existing = session.query(Chemist).filter(Chemist.code == code).first()
        if existing:
            changed = False
            if existing.shop_name != shop_name:
                existing.shop_name = shop_name
                changed = True
            if existing.contact_person != contact:
                existing.contact_person = contact
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
            chm = Chemist(
                code=code,
                shop_name=shop_name,
                contact_person=contact,
                dl_number=dl_no,
                territory_id=t.id,
                phone=f"+9198300{20000 + idx}",
                address=f"Shop {10 + idx}, Market Complex, {t.name}",
                is_active=True,
            )
            session.add(chm)
            result.created += 1

    session.flush()
    return result
