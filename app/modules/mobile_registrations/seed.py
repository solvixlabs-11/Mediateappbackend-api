"""Seed synthetic mobile registrations for dev environment."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.mobile_registrations.models import MobileRegistration
from app.modules.users.models import User


def seed_mobile_registrations(db: Session) -> int:
    """Seed at least 30 synthetic mobile registrations."""
    existing_count = db.query(MobileRegistration).count()
    if existing_count >= 30:
        return existing_count

    users = db.query(User).all()
    if not users:
        return 0

    admin = db.query(User).filter(User.email == "admin@mediate.com").first() or users[0]

    device_models = [
        "Samsung Galaxy S23",
        "Samsung Galaxy A54",
        "Xiaomi Redmi Note 12",
        "OnePlus Nord CE 3",
        "Vivo V27 Pro",
        "Realme 11 Pro",
        "Google Pixel 7a",
        "Motorola Edge 40",
    ]

    statuses = ["PENDING", "APPROVED", "REJECTED", "PENDING"]
    seeded = 0
    now = datetime.now(UTC)

    for i in range(35):
        user = users[i % len(users)]
        reg_code = f"REG-{user.employee_code or 'EMP'}-{i+101}"
        
        # Check if already exists
        exists = db.query(MobileRegistration).filter(MobileRegistration.registration_code == reg_code).first()
        if exists:
            continue

        status = statuses[i % len(statuses)]
        req_time = now - timedelta(days=(i % 14), hours=(i * 3) % 24)
        decided_time = req_time + timedelta(hours=4) if status in ("APPROVED", "REJECTED") else None
        decided_by_id = admin.id if status in ("APPROVED", "REJECTED") else None
        comment = (
            "Verified field representative device"
            if status == "APPROVED"
            else "Unregistered device serial / unauthorized model"
            if status == "REJECTED"
            else None
        )

        model = device_models[i % len(device_models)]
        raw_device = f"IMEI-8639201{i:04d}-{model}"
        device_hash = hashlib.sha256(raw_device.encode()).hexdigest()[:32]

        reg = MobileRegistration(
            registration_code=reg_code,
            employee_id=user.id,
            designation=user.role.name if user.role else "Medical Representative",
            territory="South Territory" if i % 2 == 0 else "North Territory",
            device_id_hash=device_hash,
            device_model=model,
            app_version=f"2.4.{i % 5}",
            status=status,
            requested_at=req_time,
            decided_by_id=decided_by_id,
            decided_at=decided_time,
            comment=comment,
        )
        db.add(reg)
        seeded += 1

    db.commit()
    return seeded


if __name__ == "__main__":
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        count = seed_mobile_registrations(db)
        print(f"Seeded {count} mobile registrations.")
