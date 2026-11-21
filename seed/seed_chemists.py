"""Seeder for Chemists (32 records across territories)."""

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
        ("CHM011", "Mahavir Chemist & Druggist", "Kantilal Jain", "20B-MH-102948"),
        ("CHM012", "Relief Medical Agency", "Harishankar Tiwari", "20B-MH-102949"),
        ("CHM013", "Sai Medico & General Store", "Vijay Patil", "20B-MH-102950"),
        ("CHM014", "Metro Chemist Dadar", "Hemant Kulkarni", "20B-MH-102951"),
        ("CHM015", "Shree Ram Medicals", "Ramchandra More", "20B-MH-102952"),
        ("CHM016", "New Bombay Chemists", "Sitaram Naik", "20B-MH-102953"),
        ("CHM017", "Maruti Pharma Care", "Govind Hegde", "20B-MH-102954"),
        ("CHM018", "Care & Cure Pharmacy", "Dhanraj Sethi", "20B-MH-102955"),
        ("CHM019", "City Medicos Thane", "Anand Gokhale", "20B-MH-102956"),
        ("CHM020", "Modern Drug House", "Bhagwan Das", "20B-MH-102957"),
        ("CHM021", "Poona Medical Center", "Nitin Deshpande", "20B-MH-102958"),
        ("CHM022", "Deccan Chemist", "Ajit Thorat", "20B-MH-102959"),
        ("CHM023", "Swastik Medical Store", "Babulal Shah", "20B-MH-102960"),
        ("CHM024", "Universal Druggists", "Mustafa Lokhandwala", "20B-MH-102961"),
        ("CHM025", "Navrang Chemist", "Champaklal Mehta", "20B-MH-102962"),
        ("CHM026", "Arogya Medical Store", "Vinayak Joshi", "20B-MH-102963"),
        ("CHM027", "Prabhat Pharmacy", "Devendra Singh", "20B-MH-102964"),
        ("CHM028", "HealthPlus Chemist", "Sujit Banerjee", "20B-MH-102965"),
        ("CHM029", "Gurukrupa Medical (Field Reg)", "Shrikant Salunke", "20B-MH-102966"),
        ("CHM030", "Balaji Pharma Store (Field Reg)", "Tirupati Naidu", "20B-MH-102967"),
        ("CHM031", "Aura Chemists (Field Reg)", "Sameer Sheikh", "20B-MH-102968"),
        ("CHM032", "Samarth Medical Store (Field Reg)", "Eknath Shinde", "20B-MH-102969"),
    ]

    for idx, (code, shop_name, contact, dl_no) in enumerate(sample_chemists):
        t = territories[idx % len(territories)]
        existing = session.query(Chemist).filter(Chemist.code == code).first()
        is_pending = idx >= 28  # Last 4 pending for field approvals testing

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
                changed = True
            if existing.is_active != (not is_pending):
                existing.is_active = not is_pending
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
                is_active=not is_pending,
            )
            session.add(chm)
            result.created += 1

    session.flush()
    return result
