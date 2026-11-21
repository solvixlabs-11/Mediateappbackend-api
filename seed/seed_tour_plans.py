"""Seeder for Tour Programs (32 records across field staff)."""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.modules.approvals.models import ApprovalRequest
from app.modules.tours.models import TourProgram
from app.modules.users.models import User
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="tour_plans")
    if not dev:
        return result

    users = session.query(User).filter(User.is_active == True).all()  # noqa: E712
    if not users:
        return result

    today = date.today()

    route_templates = [
        ("Mumbai Central & South Detailing", "Churchgate - Dadar Super-Core Doctors", 24),
        ("Western Suburbs Hospital Coverage", "Bandra - Andheri Multi-Specialty Hospitals", 22),
        ("Thane & Navi Mumbai Retail Drive", "Thane West - Vashi Key Chemists & Stockists", 25),
        ("Pune Urban Doctor Detailing", "Shivaji Nagar - Kothrud Consulting Physicians", 24),
        ("PCMC Industrial Belt Coverage", "Pimpri - Chinchwad Orthopedic & General Practitioners", 20),
        ("Ahmedabad Commercial Launch", "Ashram Road - SG Highway Key Cardiologists", 24),
        ("Surat Textile Belt Pharmacy Push", "Ring Road - Adajan Retail Chemists", 22),
        ("Bengaluru East Clinic Detailing", "Indiranagar - Whitefield Pediatricians", 24),
        ("South Delhi Premium Hospital Tour", "Saket - Green Park Key Specialists", 20),
        ("Central Hyderabad Endocrinology Push", "Banjara Hills - Jubilee Hills Consultants", 22),
    ]

    for idx in range(32):
        u = users[idx % len(users)]
        title, route, total_days = route_templates[idx % len(route_templates)]

        # Status distribution: 14 PENDING, 12 APPROVED, 4 REJECTED, 2 DRAFT
        if idx < 14:
            status = "PENDING"
        elif idx < 26:
            status = "APPROVED"
        elif idx < 30:
            status = "REJECTED"
        else:
            status = "DRAFT"

        month_offset = idx // 8
        tour_date = (today.replace(day=1) + timedelta(days=month_offset * 30)).replace(day=1)
        end_date = tour_date + timedelta(days=total_days - 1)

        unique_title = f"{title} #{idx + 1:02d} ({tour_date.strftime('%B %Y')})"

        existing = (
            session.query(TourProgram)
            .filter(
                TourProgram.user_id == u.id,
                TourProgram.title == unique_title,
            )
            .first()
        )
        if not existing:
            tp = TourProgram(
                user_id=u.id,
                title=unique_title,
                start_date=tour_date,
                end_date=end_date,
                total_days=total_days,
                route_details=route,
                objectives="Achieve 95%+ target coverage, focus on top-brand prescription conversion and stockist replenishment",
                status=status,
            )
            session.add(tp)
            session.flush()

            app_req = ApprovalRequest(
                entity_type="TOUR",
                entity_id=tp.id,
                requester_id=u.id,
                status=status,
                current_step=1,
                total_steps=1,
                title=f"Tour: {unique_title} ({total_days} days)",
                details=f"{tour_date} to {end_date} - Route: {route}",
            )
            session.add(app_req)
            session.flush()
            tp.approval_request_id = app_req.id
            result.created += 1
        else:
            result.unchanged += 1

    session.flush()
    return result
