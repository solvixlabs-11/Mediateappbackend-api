"""Seed initial master items, states, cities, and areas."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.modules.masters.models import Area, City, MasterItem, State

logger = logging.getLogger(__name__)

INITIAL_SPECIALIZATIONS = [
    ("CARDIO", "Cardiology", "Heart and cardiovascular specialists", 1),
    ("PEDIATRIC", "Pediatrics", "Child medical specialists", 2),
    ("DERMA", "Dermatology", "Skin, hair, and nail specialists", 3),
    ("GEN_MED", "General Medicine", "Consultant physician / internal medicine", 4),
    ("ORTHO", "Orthopedics", "Bone and joint specialists", 5),
    ("GYNEC", "Gynecology & Obstetrics", "Women's health specialists", 6),
    ("NEURO", "Neurology", "Brain and nervous system specialists", 7),
    ("ENT", "ENT (Otolaryngology)", "Ear, nose, throat specialists", 8),
    ("OPHTHAL", "Ophthalmology", "Eye care specialists", 9),
    ("GASTRO", "Gastroenterology", "Digestive system specialists", 10),
    ("PULMO", "Pulmonology", "Chest and respiratory specialists", 11),
    ("DIABETO", "Diabetology & Endocrinology", "Diabetes and metabolic specialists", 12),
]

INITIAL_CATEGORIES = [
    ("SUPER_CORE", "Super Core (VIP)", "High volume Key Opinion Leader (KOL)", 1),
    ("CORE", "Core (Tier 1)", "Regular high prescriber", 2),
    ("GENERAL", "General (Tier 2)", "Moderate prescriber", 3),
    ("POTENTIAL", "Potential (Tier 3)", "New prospect / developmental", 4),
]

INITIAL_PRIORITIES = [
    ("HIGH", "High Priority", "Weekly / Bi-weekly visit cycle", 1),
    ("MEDIUM", "Medium Priority", "Monthly visit cycle", 2),
    ("LOW", "Low Priority", "Quarterly visit cycle", 3),
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
