"""Seeder for Visits (DCR and Planned Visits)."""

import uuid
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.modules.customers.models import Doctor, Chemist
from app.modules.dcr.models import DcrVisit, PlannedVisit
from app.modules.users.models import User
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="visits")
    if not dev:
        return result

    mr_user = session.query(User).filter(User.email == "mr@mediatehealthcare.com").first()
    if not mr_user:
        mr_user = session.query(User).first()
    if not mr_user:
        return result

    doctors = session.query(Doctor).limit(10).all()
    today = date.today()
    now = datetime.utcnow()

    for idx, doc in enumerate(doctors):
        # Planned Visit
        p_existing = (
            session.query(PlannedVisit)
            .filter(
                PlannedVisit.user_id == mr_user.id,
                PlannedVisit.doctor_id == doc.id,
                PlannedVisit.plan_date == today,
            )
            .first()
        )
        if not p_existing:
            pv = PlannedVisit(
                user_id=mr_user.id,
                customer_type="DOCTOR",
                doctor_id=doc.id,
                plan_date=today,
                status="PLANNED",
                client_uuid=f"seed-pv-{mr_user.id}-{doc.id}-{today.isoformat()}",
            )
            session.add(pv)
            result.created += 1
        else:
            result.unchanged += 1

        # Completed DCR Visit
        d_existing = (
            session.query(DcrVisit)
            .filter(
                DcrVisit.user_id == mr_user.id,
                DcrVisit.doctor_id == doc.id,
                DcrVisit.dcr_date == today,
            )
            .first()
        )
        if not d_existing:
            dv = DcrVisit(
                user_id=mr_user.id,
                customer_type="DOCTOR",
                doctor_id=doc.id,
                dcr_date=today,
                call_time=now,
                visit_type="INDEPENDENT",
                pob_amount=1500.0 + (idx * 500),
                is_geofence_verified=True,
                client_uuid=f"seed-dv-{mr_user.id}-{doc.id}-{today.isoformat()}",
            )
            session.add(dv)
            result.created += 1
        else:
            result.unchanged += 1

    session.flush()
    return result

