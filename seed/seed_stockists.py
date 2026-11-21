"""Seeder for Stockists (32 records across distribution zones)."""

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
        ("STK001", "Medilink Pharma Distributors", "Vikram Lal", "27AABCM1234F1Z1", 30),
        ("STK002", "National Drug Agencies", "Harishanker Gupta", "27AABCN5678G1Z2", 45),
        ("STK003", "Apex Healthcare Distribution", "Rajendra Parekh", "27AABCA9101H1Z3", 21),
        ("STK004", "Shreeji Pharma Distributorship", "Kishore Shah", "27AABCS1121J1Z4", 30),
        ("STK005", "Vardhman Medical Agencies", "Nirmal Jain", "27AABCV3141K1Z5", 60),
        ("STK006", "Western India Pharma Agencies", "Dinesh Kothari", "27AABCW5161L1Z6", 30),
        ("STK007", "Pune Pharma Logistics", "Satish Deshmukh", "27AABCP7181M1Z7", 45),
        ("STK008", "Gujarat Medical Corporation", "Mukesh Patel", "24AABCG9201N1Z8", 30),
        ("STK009", "Karnataka Drug Syndicate", "Venkatesh Rao", "29AABCK1221P1Z9", 30),
        ("STK010", "Delhi Pharma Wholesalers", "Subhash Aggarwal", "07AABCD3241Q1ZA", 45),
        ("STK011", "Royal Medical Distributors", "Kalyan Banerjee", "27AABCR5261R1ZB", 30),
        ("STK012", "Sun Healthcare Supplies", "Pradeep Agrawal", "27AABCS7281S1ZC", 21),
        ("STK013", "Om Sai Drug House", "Gopalakrishnan Nair", "27AABCO9301T1ZD", 30),
        ("STK014", "Metro Lifesciences Agencies", "Mahendra Bohra", "27AABCM1321U1ZE", 45),
        ("STK015", "Bharat Pharma Distributors", "Rameshwar Dayal", "27AABCB3341V1ZF", 30),
        ("STK016", "Universal Medical Syndicate", "Tanveer Alam", "27AABCU5361W1ZG", 30),
        ("STK017", "Deccan Distributors & Co.", "Balu Jagtap", "27AABCD7381X1ZH", 45),
        ("STK018", "Prestige Medical Agencies", "Jayantilal Gada", "27AABCP9401Y1ZI", 30),
        ("STK019", "Navkar Pharma Distributorship", "Parasmal Doshi", "27AABCN1421Z1ZJ", 60),
        ("STK020", "Sterling Healthcare Distribution", "Deepak Chokshi", "27AABCS3441A1ZK", 21),
        ("STK021", "Standard Drug Distributors", "Madan Mohan Sharma", "27AABCS5461B1ZL", 30),
        ("STK022", "Alpha Medical Distributors", "Chandrashekhar Joshi", "27AABCA7481C1ZM", 30),
        ("STK023", "Pioneer Pharma Lines", "Vinodrai Mehta", "27AABCP9501D1ZN", 45),
        ("STK024", "Crown Medical Agency", "Kulbhushan Anand", "27AABCC1521E1ZO", 30),
        ("STK025", "Star Drug House", "Murlidhar Rathi", "27AABCS3541F1ZP", 30),
        ("STK026", "Arogyam Distributors", "Shivajirao Patil", "27AABCA5561G1ZQ", 45),
        ("STK027", "Central Pharma Corporation", "Hasmukhlal Trivedi", "27AABCC7581H1ZR", 30),
        ("STK028", "United Healthcare Agencies", "Sanjeev Malhotra", "27AABCU9601I1ZS", 21),
        ("STK029", "Kuber Medical Agency (Field Reg)", "Dhanpatrai Singhania", "27AABCK1621J1ZT", 30),
        ("STK030", "Gajanan Pharma (Field Reg)", "Gajanan Sonawane", "27AABCG3641K1ZU", 30),
        ("STK031", "Siddhivinayak Medico (Field Reg)", "Sharadchandra Pawar", "27AABCS5661L1ZV", 30),
        ("STK032", "Navchetan Drug Lines (Field Reg)", "Bipin Bihari Das", "27AABCN7681M1ZW", 45),
    ]

    for idx, (code, agency, contact, gst, credit) in enumerate(sample_stockists):
        t = territories[idx % len(territories)]
        existing = session.query(Stockist).filter(Stockist.code == code).first()
        is_pending = idx >= 28  # Last 4 pending for field approvals testing

        if existing:
            changed = False
            if existing.agency_name != agency:
                existing.agency_name = agency
                changed = True
            if existing.contact_person != contact:
                existing.contact_person = contact
                changed = True
            if existing.gstin != gst:
                existing.gstin = gst
                changed = True
            if existing.credit_days != credit:
                existing.credit_days = credit
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
            stk = Stockist(
                code=code,
                agency_name=agency,
                contact_person=contact,
                gstin=gst,
                credit_days=credit,
                territory_id=t.id,
                phone=f"+9198400{30000 + idx}",
                address=f"Godown {1 + idx}, Wholesale Pharma Market, {t.name}",
                is_active=not is_pending,
            )
            session.add(stk)
            result.created += 1

    session.flush()
    return result
