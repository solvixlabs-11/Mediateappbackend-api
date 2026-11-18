"""Seeder for Stockists."""

from sqlalchemy.orm import Session
from app.modules.customers.models import Stockist
from app.modules.territories.models import Territory
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="stockists")
    territories = session.query(Territory).all()
    if not territories:
        return result

    sample_stockists = [
        ("STK001", "Mahavir Pharma Distributors", "Babulal Mehta", "27AAACM1234F1Z1", 30),
        ("STK002", "Arihant Medical Agencies", "Dinesh Jain", "27AAACA5678G2Z2", 21),
        ("STK003", "Apex Healthcare Distribution", "Sunil Deshpande", "27AAACA9012H3Z3", 45),
        ("STK004", "Shreeji Pharma Wholesalers", "Naveen Shah", "27AAACS3456I4Z4", 30),
        ("STK005", "Pune Central Pharma Distributors", "Sambhaji Gaikwad", "27AAACP7890J5Z5", 30),
        ("STK006", "Gujarat Pharma Agency", "Harshad Patel", "24AAACG1234K6Z6", 28),
        ("STK007", "Karnataka Drug House", "Venkatesh Murthy", "29AAACK5678L7Z7", 30),
        ("STK008", "Delhi National Distributors", "Rajeev Bhatia", "07AAACD9012M8Z8", 15),
    ]

    for idx, (code, agency, contact, gst, credit) in enumerate(sample_stockists):
        t = territories[idx % len(territories)]
        existing = session.query(Stockist).filter(Stockist.code == code).first()
        if existing:
            changed = False
            if existing.agency_name != agency:
                existing.agency_name = agency
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
            stk = Stockist(
                code=code,
                agency_name=agency,
                contact_person=contact,
                gstin=gst,
                credit_days=credit,
                territory_id=t.id,
                phone=f"+9198400{30000 + idx}",
                address=f"Godown {1 + idx}, Wholesale Pharma Market, {t.name}",
                is_active=True,
            )
            session.add(stk)
            result.created += 1

    session.flush()
    return result
