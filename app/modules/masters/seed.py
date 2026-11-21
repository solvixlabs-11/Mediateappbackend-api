"""Seed initial master items, states, cities, and areas."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.modules.masters.models import Area, City, MasterItem, State

logger = logging.getLogger(__name__)

INITIAL_SPECIALIZATIONS = [
    ("B_PHARM", "B-PHARM", "Bachelor of Pharmacy", 1),
    ("BAMS", "BAMS", "Ayurvedic Medicine", 2),
    ("BDS", "BDS", "Dental Surgery", 3),
    ("BHMS", "BHMS", "Homeopathic Medicine", 4),
    ("CONSULTANT_PHY", "CONSULTANT PHYSICIAN", "Consultant Physician", 5),
    ("CP", "CP", "Clinical Practitioner", 6),
    ("DENTIST", "DENTIST", "Dentist", 7),
    ("DGO", "DGO", "Gynecology & Obstetrics", 8),
    ("DNB", "DNB", "National Board Diplomate", 9),
    ("ENT", "ENT", "Ear Nose Throat", 10),
    ("CARDIO", "Cardiology", "Heart and cardiovascular specialists", 11),
    ("PEDIATRIC", "Pediatrics", "Child medical specialists", 12),
    ("DERMA", "Dermatology", "Skin, hair, and nail specialists", 13),
    ("GEN_MED", "General Medicine", "Consultant physician / internal medicine", 14),
    ("ORTHO", "Orthopedics", "Bone and joint specialists", 15),
    ("GYNEC", "Gynecology & Obstetrics", "Women's health specialists", 16),
    ("NEURO", "Neurology", "Brain and nervous system specialists", 17),
    ("OPHTHAL", "Ophthalmology", "Eye care specialists", 18),
    ("GASTRO", "Gastroenterology", "Digestive system specialists", 19),
    ("PULMO", "Pulmonology", "Chest and respiratory specialists", 20),
    ("DIABETO", "Diabetology & Endocrinology", "Diabetes and metabolic specialists", 21),
]

INITIAL_CATEGORIES = [
    ("EVENING", "EVENING", "Evening visiting slot category", 1),
    ("GYN", "GYN", "Gynecology focus category", 2),
    ("MORNING", "MORNING", "Morning visiting slot category", 3),
    ("N", "N", "Normal category", 4),
    ("PHY", "PHY", "Physician focused category", 5),
    ("SUPER_CORE", "Super Core (VIP)", "High volume Key Opinion Leader (KOL)", 6),
    ("CORE", "Core (Tier 1)", "Regular high prescriber", 7),
    ("GENERAL", "General (Tier 2)", "Moderate prescriber", 8),
    ("POTENTIAL", "Potential (Tier 3)", "New prospect / developmental", 9),
]

INITIAL_DOCTOR_MEETING_TYPES = [
    ("AFTER_2", "AFTER 2 O CL", "After 2 O'clock meeting slot", 1),
    ("AFTERNOON", "AFTERNOON", "Afternoon slot", 2),
    ("EVENING", "EVENING", "Evening slot", 3),
    ("MORNING", "MORNING", "Morning slot", 4),
    ("NIGHT", "NIGHT", "Night slot", 5),
    ("NOON", "NOON", "Noon slot", 6),
]

INITIAL_VISIT_TYPES = [
    ("GROUP_PROMO", "GROUP PROMOTIONAL CALL", "Group promotional call", 1),
    ("REGULAR_SAMPLE", "REGULAR SAMPLE CALL", "Regular sample call", 2),
    ("REMINDER", "REMINDER", "Reminder call", 3),
]

INITIAL_DIVISIONS = [
    ("MEDIATE", "MEDIATE", "Mediate Healthcare Primary Operations Division", 1),
    ("CARDIA", "Cardia Care", "Cardiovascular therapy formulations", 2),
    ("NEURO", "Neuro Science", "Neurological and CNS therapeutics", 3),
    ("DIABETES", "Diabetes & Metabolism", "Endocrinology and metabolic solutions", 4),
    ("GENERAL", "General Medicine", "Primary healthcare and general formulations", 5),
]

INITIAL_DESIGNATIONS = [
    ("ADMIN", "ADMIN", "System Administrator", 1),
    ("ARBH", "ARBH - Assi. Regional Business Head", "Assistant Regional Business Head", 2),
    ("BH", "BH - Business Head", "Business Head", 3),
    ("DBH", "DBH - Divisional Business Head", "Divisional Business Head", 4),
    ("DIRECTOR", "DIRECTOR", "Director", 5),
    ("MD", "MD", "Managing Director", 6),
    ("MR", "MR", "Medical Representative", 7),
    ("RBH", "RBH", "Regional Business Head", 8),
    ("ZBM", "ZBM", "Zonal Business Manager", 9),
    ("ASM", "Area Sales Manager", "First line sales manager", 10),
    ("RSM", "Regional Sales Manager", "Regional territory head", 11),
    ("ZSM", "Zonal Sales Manager", "Zonal territory leader", 12),
    ("NSM", "National Sales Manager", "Pan-India sales head", 13),
]

INITIAL_QUALIFICATIONS = [
    ("DGO", "DGO", "Diploma in Gynecology and Obstetrics", 1),
    ("MBBS_MS", "MBBS MS", "MBBS with Master of Surgery", 2),
    ("MBBS_DGO", "MBBS, DGO", "MBBS with DGO", 3),
    ("MD", "MD", "Doctor of Medicine", 4),
    ("MS", "MS", "Master of Surgery", 5),
    ("MBBS_MD", "MBBA-MD", "MBBS MD combined", 6),
    ("MS_DCO", "MS DCO", "MS DCO", 7),
    ("BAMS", "BAMS", "Ayurvedic Medicine & Surgery", 8),
    ("BAMS_GYN", "BAMS GYN", "BAMS Gynecology", 9),
    ("BDS", "BDS", "Dental Surgery", 10),
    ("BHMS", "BHMS", "Homeopathic Medicine & Surgery", 11),
    ("DNB", "DNB", "Diplomate of National Board", 12),
]

INITIAL_PRIORITIES = [
    ("HIGH", "High Priority", "Weekly / Bi-weekly visit cycle", 1),
    ("MEDIUM", "Medium Priority", "Monthly visit cycle", 2),
    ("LOW", "Low Priority", "Quarterly visit cycle", 3),
]

INITIAL_ZONES = [
    ("NORTH", "North Zone", "Northern states and territories", 1),
    ("SOUTH", "South Zone", "Southern states and territories", 2),
    ("EAST", "East Zone", "Eastern states and territories", 3),
    ("WEST", "West Zone", "Western states and territories", 4),
    ("CENTRAL", "Central Zone", "Central states and territories", 5),
]

INITIAL_CITY_TIERS = [
    ("METRO", "Metro", "Tier-0 Metropolitan cities", 1),
    ("TIER_1", "Tier 1", "Major urban commerce hubs", 2),
    ("TIER_2", "Tier 2", "Developing district cities", 3),
    ("TIER_3", "Tier 3", "Semi-urban / Rural beats", 4),
]

INITIAL_HOSPITAL_TYPES = [
    ("GOVERNMENT", "Government Hospital", "Public state and central facilities", 1),
    ("PRIVATE", "Private Multi-speciality", "Private corporate hospitals", 2),
    ("NURSING_HOME", "Nursing Home", "Private small to mid bed clinics", 3),
    ("TRUST", "Trust Hospital", "Charitable and trust run medical institutes", 4),
]

INITIAL_DIVISIONS = [
    ("CARDIA", "Cardia Care", "Cardiovascular therapy formulations", 1),
    ("NEURO", "Neuro Science", "Neurological and CNS therapeutics", 2),
    ("DIABETES", "Diabetes & Metabolism", "Endocrinology and metabolic solutions", 3),
    ("GENERAL", "General Medicine", "Primary healthcare and general formulations", 4),
]

INITIAL_DESIGNATIONS = [
    ("MR", "Medical Representative", "Frontline field sales executive", 1),
    ("ASM", "Area Sales Manager", "First line sales manager", 2),
    ("RSM", "Regional Sales Manager", "Regional territory head", 3),
    ("ZSM", "Zonal Sales Manager", "Zonal territory leader", 4),
    ("NSM", "National Sales Manager", "Pan-India sales head", 5),
]

INITIAL_QUALIFICATIONS = [
    ("MD", "MD (Doctor of Medicine)", "Postgraduate medical degree", 1),
    ("MBBS", "MBBS", "Bachelor of Medicine & Surgery", 2),
    ("MS", "MS (Master of Surgery)", "Postgraduate surgical specialization", 3),
    ("DNB", "DNB", "Diplomate of National Board", 4),
    ("BAMS", "BAMS", "Ayurvedic Medicine & Surgery", 5),
    ("BHMS", "BHMS", "Homeopathic Medicine & Surgery", 6),
    ("BDS", "BDS", "Dental Surgery", 7),
    ("MCH", "MCh (Magister Chirurgiae)", "Super-speciality surgical degree", 8),
    ("DM", "DM (Doctorate of Medicine)", "Super-speciality medical degree", 9),
    ("DGO", "DGO", "Diploma in Gynecology and Obstetrics", 10),
]

INITIAL_DOCTOR_TYPES = [
    ("CONSULTANT", "Consultant Physician", "Visiting or senior consultant", 1),
    ("SURGEON", "Surgeon", "Operative surgical specialist", 2),
    ("PHYSICIAN", "Physician", "Primary care physician", 3),
    ("CLINIC_OWNER", "Private Clinic Owner", "Independent private practice", 4),
    ("HOSPITAL_OPD", "Hospital OPD Doctor", "Institutional OPD doctor", 5),
    ("GOVT_DOCTOR", "Government Doctor", "Public healthcare medical officer", 6),
]

INITIAL_STORE_TYPES = [
    ("RETAIL_PHARMACY", "Retail Pharmacy", "Local retail chemist shop", 1),
    ("HOSPITAL_ATTACHED", "Hospital Attached Chemist", "In-house hospital pharmacy counter", 2),
    ("WHOLESALE_RETAIL", "Wholesale & Retail", "Semi-wholesale and OTC counter", 3),
    ("CHAIN_PHARMACY", "Chain Pharmacy", "Corporate retail pharmacy chain", 4),
    ("GENERIC_STORE", "Generic Drug Store", "Affordable generic medicine outlet", 5),
]

INITIAL_DISTRIBUTOR_TYPES = [
    ("FULL_LINE_STOCKIST", "Full-Line Pharma Stockist", "Comprehensive multi-company distributor", 1),
    ("EXCLUSIVE_FRANCHISE", "Exclusive Franchise", "Authorized single-brand franchise distributor", 2),
    ("SEMI_WHOLESALE", "Semi-Wholesale Depot", "Regional wholesale redistribution hub", 3),
    ("HOSPITAL_SUPPLY", "Hospital Supply Distributor", "Institutional government & hospital supplier", 4),
    ("GENERIC_DEPOT", "Generic Medicine Stockist", "Trade generic pharmaceuticals distributor", 5),
]

INITIAL_CREDIT_TERMS = [
    ("DAYS_15", "15 Days Credit", "Standard 15-day payment cycle", 1),
    ("DAYS_21", "21 Days Standard", "21-day regular billing term", 2),
    ("DAYS_30", "30 Days Credit", "Monthly 30-day settlement", 3),
    ("DAYS_45", "45 Days Extended", "Extended 45-day institutional term", 4),
    ("ADVANCE_PDC", "PDC / Advance Only", "Post-dated cheque or 100% advance", 5),
]

INITIAL_EXPENSE_TYPES = [
    ("DAILY_ALLOWANCE", "Daily Allowance (DA)", "Daily standard meal/allowance in territory", 1),
    ("TRAVEL_FARE", "Travel Fare (TA)", "Bus, rail, or taxi transit fare reimbursement", 2),
    ("LODGING", "Hotel / Lodging", "Outstation hotel accommodation bill", 3),
    ("MISCELLANEOUS", "Miscellaneous", "Printing, courier, and stationery charges", 4),
]

INITIAL_CUSTOMER_TYPES = [
    ("DOCTOR", "Doctor", "Medical practitioners and clinical specialists", 1),
    ("CHEMIST", "Chemist", "Retail pharmacies and medical shops", 2),
    ("HOSPITAL", "Hospital", "Healthcare institutions and nursing homes", 3),
    ("STOCKIST", "Stockist", "Distribution partners and wholesalers", 4),
]

INITIAL_APPROVAL_STATUSES = [
    ("PENDING", "Pending", "Awaiting manager review", 1),
    ("APPROVED", "Approved", "Authorized by reporting manager", 2),
    ("REJECTED", "Rejected", "Declined with feedback", 3),
    ("VERIFIED", "Verified", "Field verified by manager / audit", 4),
]

INITIAL_GEOGRAPHY: list[dict[str, Any]] = [
    {
        "state_name": "Maharashtra",
        "state_code": "MH",
        "cities": [
            {
                "city_name": "Mumbai",
                "city_code": "MUM",
                "areas": [
                    ("Andheri West", "400058"),
                    ("Bandra West", "400050"),
                    ("Dadar", "400014"),
                    ("Borivali West", "400092"),
                    ("Goregaon East", "400063"),
                ],
            },
            {
                "city_name": "Pune",
                "city_code": "PUN",
                "areas": [
                    ("Shivajinagar", "411005"),
                    ("Kothrud", "411038"),
                    ("Hinjewadi", "411057"),
                    ("Viman Nagar", "411014"),
                ],
            },
        ],
    },
    {
        "state_name": "Delhi",
        "state_code": "DL",
        "cities": [
            {
                "city_name": "New Delhi",
                "city_code": "DEL",
                "areas": [
                    ("Connaught Place", "110001"),
                    ("South Extension", "110049"),
                    ("Rohini", "110085"),
                    ("Dwarka", "110075"),
                ],
            }
        ],
    },
    {
        "state_name": "Karnataka",
        "state_code": "KA",
        "cities": [
            {
                "city_name": "Bengaluru",
                "city_code": "BLR",
                "areas": [
                    ("Koramangala", "560034"),
                    ("Indiranagar", "560038"),
                    ("Jayanagar", "560041"),
                    ("Whitefield", "560066"),
                ],
            }
        ],
    },
]


def seed_masters(db: Session) -> None:
    """Seed business master items and geography."""
    # 1. Master Items: Specializations
    for code, name, desc, order in INITIAL_SPECIALIZATIONS:
        item = (
            db.query(MasterItem)
            .filter(MasterItem.type == "SPECIALIZATION", MasterItem.code == code)
            .first()
        )
        if not item:
            db.add(
                MasterItem(
                    type="SPECIALIZATION",
                    code=code,
                    name=name,
                    description=desc,
                    sort_order=order,
                )
            )

    # 2. Master Items: Categories
    for code, name, desc, order in INITIAL_CATEGORIES:
        item = (
            db.query(MasterItem)
            .filter(MasterItem.type == "CUSTOMER_CATEGORY", MasterItem.code == code)
            .first()
        )
        if not item:
            db.add(
                MasterItem(
                    type="CUSTOMER_CATEGORY",
                    code=code,
                    name=name,
                    description=desc,
                    sort_order=order,
                )
            )

    # 3. Master Items: Priorities
    for code, name, desc, order in INITIAL_PRIORITIES:
        item = (
            db.query(MasterItem)
            .filter(MasterItem.type == "VISIT_PRIORITY", MasterItem.code == code)
            .first()
        )
        if not item:
            db.add(
                MasterItem(
                    type="VISIT_PRIORITY",
                    code=code,
                    name=name,
                    description=desc,
                    sort_order=order,
                )
            )

    # 4. Master Items: Zones
    for code, name, desc, order in INITIAL_ZONES:
        item = db.query(MasterItem).filter(MasterItem.type == "ZONE", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="ZONE", code=code, name=name, description=desc, sort_order=order))

    # 5. Master Items: City Tiers
    for code, name, desc, order in INITIAL_CITY_TIERS:
        item = db.query(MasterItem).filter(MasterItem.type == "CITY_TIER", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="CITY_TIER", code=code, name=name, description=desc, sort_order=order))

    # 6. Master Items: Hospital Types
    for code, name, desc, order in INITIAL_HOSPITAL_TYPES:
        item = db.query(MasterItem).filter(MasterItem.type == "HOSPITAL_TYPE", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="HOSPITAL_TYPE", code=code, name=name, description=desc, sort_order=order))

    # 7. Master Items: Divisions
    for code, name, desc, order in INITIAL_DIVISIONS:
        item = db.query(MasterItem).filter(MasterItem.type == "DIVISION", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="DIVISION", code=code, name=name, description=desc, sort_order=order))

    # 8. Master Items: Designations
    for code, name, desc, order in INITIAL_DESIGNATIONS:
        item = db.query(MasterItem).filter(MasterItem.type == "DESIGNATION", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="DESIGNATION", code=code, name=name, description=desc, sort_order=order))

    # 9. Master Items: Qualifications
    for code, name, desc, order in INITIAL_QUALIFICATIONS:
        item = db.query(MasterItem).filter(MasterItem.type == "QUALIFICATION", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="QUALIFICATION", code=code, name=name, description=desc, sort_order=order))

    # 10. Master Items: Doctor Types
    for code, name, desc, order in INITIAL_DOCTOR_TYPES:
        item = db.query(MasterItem).filter(MasterItem.type == "DOCTOR_TYPE", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="DOCTOR_TYPE", code=code, name=name, description=desc, sort_order=order))

    # 11. Master Items: Store Types (Chemists)
    for code, name, desc, order in INITIAL_STORE_TYPES:
        item = db.query(MasterItem).filter(MasterItem.type == "STORE_TYPE", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="STORE_TYPE", code=code, name=name, description=desc, sort_order=order))

    # 12. Master Items: Distributor Types (Stockists)
    for code, name, desc, order in INITIAL_DISTRIBUTOR_TYPES:
        item = db.query(MasterItem).filter(MasterItem.type == "DISTRIBUTOR_TYPE", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="DISTRIBUTOR_TYPE", code=code, name=name, description=desc, sort_order=order))

    # 13. Master Items: Credit Terms
    for code, name, desc, order in INITIAL_CREDIT_TERMS:
        item = db.query(MasterItem).filter(MasterItem.type == "CREDIT_TERMS", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="CREDIT_TERMS", code=code, name=name, description=desc, sort_order=order))

    # 14. Master Items: Expense Types
    for code, name, desc, order in INITIAL_EXPENSE_TYPES:
        item = db.query(MasterItem).filter(MasterItem.type == "EXPENSE_TYPE", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="EXPENSE_TYPE", code=code, name=name, description=desc, sort_order=order))

    # 15. Master Items: Customer Types
    for code, name, desc, order in INITIAL_CUSTOMER_TYPES:
        item = db.query(MasterItem).filter(MasterItem.type == "CUSTOMER_TYPE", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="CUSTOMER_TYPE", code=code, name=name, description=desc, sort_order=order))

    # 16. Master Items: Approval Statuses
    for code, name, desc, order in INITIAL_APPROVAL_STATUSES:
        item = db.query(MasterItem).filter(MasterItem.type == "APPROVAL_STATUS", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="APPROVAL_STATUS", code=code, name=name, description=desc, sort_order=order))

    # 17. Master Items: Doctor Meeting Types
    for code, name, desc, order in INITIAL_DOCTOR_MEETING_TYPES:
        item = db.query(MasterItem).filter(MasterItem.type == "DOCTOR_MEETING_TYPE", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="DOCTOR_MEETING_TYPE", code=code, name=name, description=desc, sort_order=order))

    # 18. Master Items: Visit Types
    for code, name, desc, order in INITIAL_VISIT_TYPES:
        item = db.query(MasterItem).filter(MasterItem.type == "VISIT_TYPE", MasterItem.code == code).first()
        if not item:
            db.add(MasterItem(type="VISIT_TYPE", code=code, name=name, description=desc, sort_order=order))

    # 19. Provisional Masters (Wave W6)
    from app.modules.masters.seed_provisional import seed_provisional_masters
    seed_provisional_masters(db)

    db.flush()

    # 4. Geography (States -> Cities -> Areas)
    for state_data in INITIAL_GEOGRAPHY:
        state = db.query(State).filter(State.code == state_data["state_code"]).first()
        if not state:
            state = State(name=state_data["state_name"], code=state_data["state_code"])
            db.add(state)
            db.flush()

        for city_data in state_data["cities"]:
            city = (
                db.query(City)
                .filter(City.state_id == state.id, City.name == city_data["city_name"])
                .first()
            )
            if not city:
                city = City(
                    state_id=state.id,
                    name=city_data["city_name"],
                    code=city_data["city_code"],
                )
                db.add(city)
                db.flush()

            for area_name, pincode in city_data["areas"]:
                area = (
                    db.query(Area).filter(Area.city_id == city.id, Area.name == area_name).first()
                )
                if not area:
                    area = Area(city_id=city.id, name=area_name, pincode=pincode)
                    db.add(area)

    db.commit()
    logger.info("Masters seeding completed successfully.")
