"""Seed provisional values for the 5 unverified masters (Wave W6).

The 5 masters:
1. ATTACHMENT_TYPE: Customer KYC & verification document types
2. DOCTOR_TYPE: Doctor operational classification (Consultant, RMO, GP, Super Specialist)
3. SUPPLIER: Distributors / Vendors supplying pharmaceutical products
4. HOSPITAL_CATEGORY: Tertiary, Super-Specialty, Nursing Home, Community
5. PRODUCT_GALLERY: Digital detailing visual aids, clinical trial slides, pack shots
"""

import logging
from sqlalchemy.orm import Session
from app.modules.masters.models import MasterItem

logger = logging.getLogger(__name__)

PROVISIONAL_MASTERS = [
    # 1. ATTACHMENT_TYPE
    ("ATTACHMENT_TYPE", "KYC_PAN", "PAN Card Verification", "Customer PAN card copy for verification & compliance", 1),
    ("ATTACHMENT_TYPE", "KYC_AADHAAR", "Aadhaar Card Copy", "Identity verification document", 2),
    ("ATTACHMENT_TYPE", "DRUG_LICENSE", "Drug License Copy", "Form 20B/21B retail/wholesale drug license copy", 3),
    ("ATTACHMENT_TYPE", "GST_CERT", "GST Certificate", "GST registration certificate", 4),
    ("ATTACHMENT_TYPE", "CLINIC_PHOTO", "Clinic / Shop Front Photo", "Geo-tagged photo of customer premises", 5),

    # 2. DOCTOR_TYPE
    ("DOCTOR_TYPE", "CONSULTANT", "Consultant Doctor", "Senior hospital/private consultant", 1),
    ("DOCTOR_TYPE", "RMO", "Resident Medical Officer", "Hospital residential staff doctor", 2),
    ("DOCTOR_TYPE", "GP", "General Practitioner", "Neighborhood primary care physician", 3),
    ("DOCTOR_TYPE", "SUPER_SPEC", "Super Specialist", "DM / MCh specialized doctor", 4),

    # 3. SUPPLIER
    ("SUPPLIER", "SUP_CIPLA", "Cipla Distribution Hub", "Bulk finished goods supplier", 1),
    ("SUPPLIER", "SUP_SUN", "Sun Pharma C&F", "Regional consignment & forwarding agent", 2),
    ("SUPPLIER", "SUP_TORRENT", "Torrent Logistics", "Primary distributor", 3),

    # 4. HOSPITAL_CATEGORY
    ("HOSPITAL_CATEGORY", "GOVT_TERTIARY", "Government Tertiary Hospital", "State medical college & hospital", 1),
    ("HOSPITAL_CATEGORY", "PVT_SUPER", "Private Super-Specialty", "Multi-specialty corporate hospital", 2),
    ("HOSPITAL_CATEGORY", "NURSING_HOME", "Nursing Home / Day Care", "Local surgical nursing home", 3),
    ("HOSPITAL_CATEGORY", "COMMUNITY_CLINIC", "Community Health Center", "Primary healthcare center", 4),

    # 5. PRODUCT_GALLERY
    ("PRODUCT_GALLERY", "SLIDE_MEDICAR_01", "Medicar-500 Mechanism of Action", "Visual detailing slide on active therapeutic action", 1),
    ("PRODUCT_GALLERY", "SLIDE_CLINICAL_02", "Clinical Trial Phase III Efficacy", "Double-blind comparative efficacy study slide", 2),
    ("PRODUCT_GALLERY", "PACK_SHOT_3D", "Medicar Pack Shot & Blister 3D", "Packaging visuals and dosage guidelines", 3),
]


def seed_provisional_masters(db: Session) -> None:
    """Seed provisional items with is_provisional=True."""
    for item_type, code, name, desc, order in PROVISIONAL_MASTERS:
        existing = (
            db.query(MasterItem)
            .filter(MasterItem.type == item_type, MasterItem.code == code)
            .first()
        )
        if not existing:
            item = MasterItem(
                type=item_type,
                code=code,
                name=name,
                description=desc,
                sort_order=order,
                is_provisional=True,
            )
            db.add(item)
            db.flush()
        else:
            existing.is_provisional = True
            db.flush()
    db.commit()
    logger.info("Provisional masters seeded successfully.")
