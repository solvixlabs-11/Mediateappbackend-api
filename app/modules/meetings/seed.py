"""Seed synthetic meetings for 3-tile workflow inbox."""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.modules.meetings.models import Meeting
from app.modules.users.models import User

logger = logging.getLogger(__name__)


def seed_meetings(db: Session) -> None:
    """Idempotently seed demo cycle meetings and reviews."""
    admin = db.query(User).filter(User.email == "admin@mediatehealthcare.com").first()
    manager = db.query(User).filter(User.email == "manager@mediatehealthcare.com").first()
    mr = db.query(User).filter(User.email == "mr@mediatehealthcare.com").first()

    if not admin or not manager:
        return

    now = datetime.utcnow()

    demo_meetings = [
        # Draft by manager
        {
            "agenda": "Q1 Territory Review - Pune East",
            "meeting_type": "BUSINESS_REVIEW",
            "start_date": now + timedelta(days=2, hours=10),
            "end_date": now + timedelta(days=2, hours=12),
            "created_by_id": manager.id,
            "organiser_id": manager.id,
            "location": "Pune Divisional Office",
            "status": "DRAFT",
            "remarks": "Reviewing target vs achievement for Q1",
        },
        # Applied by manager (received by admin)
        {
            "agenda": "Monthly Sales Cycle Review - West Zone",
            "meeting_type": "CYCLE_MEETING",
            "start_date": now + timedelta(days=5, hours=9),
            "end_date": now + timedelta(days=5, hours=17),
            "created_by_id": manager.id,
            "organiser_id": admin.id,
            "location": "Hotel Grand Central, Mumbai",
            "status": "APPLIED",
            "remarks": "Cycle meeting for west zone MRs and managers",
        },
        # Applied by MR (received by manager)
        {
            "agenda": "Product Detailing Workshop - Medicar 500",
            "meeting_type": "FIELD_TRAINING",
            "start_date": now + timedelta(days=7, hours=14),
            "end_date": now + timedelta(days=7, hours=16),
            "created_by_id": mr.id if mr else manager.id,
            "organiser_id": manager.id,
            "location": "Webinar / Google Meet",
            "status": "APPLIED",
            "remarks": "Special clinical detailing training",
        },
        # Approved meeting
        {
            "agenda": "Annual Operations Strategy Conference 2026",
            "meeting_type": "ANNUAL_CONFERENCE",
            "start_date": now + timedelta(days=15, hours=10),
            "end_date": now + timedelta(days=16, hours=18),
            "created_by_id": admin.id,
            "organiser_id": admin.id,
            "location": "Convention Centre, New Delhi",
            "status": "APPROVED",
            "remarks": "All-India field force annual summit",
        },
    ]

    for m in demo_meetings:
        existing = (
            db.query(Meeting)
            .filter(Meeting.agenda == m["agenda"])
            .first()
        )
        if not existing:
            db.add(Meeting(**m))

    db.commit()
    logger.info("Demo meetings seeded successfully.")
