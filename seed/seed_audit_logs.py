"""Seeder for Audit Trail (60+ synthetic events across 30 days)."""

import datetime as dt
import random
from sqlalchemy.orm import Session
from app.modules.common.models import AuditLog
from app.modules.users.models import User
from seed.base import SeedResult

# Seed configuration
TOTAL_AUDIT_EVENTS = 75
RANDOM_SEED = 42

MODULES_ACTIONS = [
    ("AUTH", "LOGIN", "User logged in successfully from Web Portal", "SUCCESS"),
    ("AUTH", "LOGIN", "User logged in successfully from Mobile App", "SUCCESS"),
    ("AUTH", "LOGIN_FAILED", "Invalid password attempt for account ******4829", "FAILED"),
    ("AUTH", "LOGOUT", "User logged out of active session", "SUCCESS"),
    ("MASTERS", "CREATE", "Created new Area record in territory master", "SUCCESS"),
    ("MASTERS", "UPDATE", "Updated pin-code and jurisdiction for City", "SUCCESS"),
    ("CUSTOMERS", "CREATE", "Registered new Doctor record with primary clinic", "SUCCESS"),
    ("CUSTOMERS", "UPDATE", "Updated visiting hours and category for Doctor", "SUCCESS"),
    ("CUSTOMERS", "APPROVE", "Manager approved field registration for Chemist", "SUCCESS"),
    ("ATTENDANCE", "CREATE", "Morning field check-in punch recorded with GPS telemetry", "SUCCESS"),
    ("ATTENDANCE", "UPDATE", "End-of-day check-out punch recorded", "SUCCESS"),
    ("DCR", "CREATE", "Field visit call report submitted with sample detailing", "SUCCESS"),
    ("DCR", "APPROVE", "Manager approved DCR call report", "SUCCESS"),
    ("EXPENSE", "CREATE", "Field expense claim submitted for Daily Allowance", "SUCCESS"),
    ("EXPENSE", "APPROVE", "Manager approved reimbursement claim", "SUCCESS"),
    ("EXPENSE", "REJECT", "Manager rejected claim: Missing mandatory tax invoice receipt", "SUCCESS"),
    ("ORDERS", "CREATE", "Stockist primary purchase booking created", "SUCCESS"),
    ("SETTINGS", "UPDATE", "Updated geofence radius policy for Doctor customer type", "SUCCESS"),
    ("SETTINGS", "CONFIRM", "Confirmed provisional daily attendance cut-off time", "SUCCESS"),
    ("MAPPINGS", "MAPPING_APPLY", "Bulk territory assignment wizard batch applied", "SUCCESS"),
    ("AUDIT", "EXPORT", "Administrator exported 90-day compliance logs in CSV format", "SUCCESS"),
]

CHANNELS = ["WEB", "MOBILE", "SYSTEM"]


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="audit_logs")
    existing_count = session.query(AuditLog).count()
    if existing_count >= TOTAL_AUDIT_EVENTS:
        result.unchanged = existing_count
        return result

    rng = random.Random(RANDOM_SEED)
    users = session.query(User).all()
    user_ids = [u.id for u in users] if users else [1]

    now = dt.datetime.now(dt.timezone.utc)

    # Calculate events to generate
    needed = TOTAL_AUDIT_EVENTS - existing_count
    for i in range(needed):
        mod, act, summary, res = rng.choice(MODULES_ACTIONS)
        uid = rng.choice(user_ids)
        chan = rng.choice(CHANNELS)
        days_ago = rng.randint(0, 29)
        hours_ago = rng.randint(0, 23)
        mins_ago = rng.randint(0, 59)
        event_time = now - dt.timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)

        ip = f"192.168.1.{rng.randint(10, 250)}"
        req_id = f"req-{rng.randint(100000, 999999)}"

        log = AuditLog(
            user_id=uid,
            module=mod,
            action=act,
            entity_type=mod.title(),
            entity_id=str(rng.randint(101, 999)),
            channel=chan,
            request_id=req_id,
            result=res,
            summary=summary,
            details=f"Synthetic audit event #{i+1} generated for test verification.",
            before_json='{"status": "OLD", "token": "******", "phone": "******9182"}' if act == "UPDATE" else None,
            after_json='{"status": "NEW", "token": "******", "phone": "******9182"}' if act in ["CREATE", "UPDATE"] else None,
            ip_address=ip,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
        )
        # Set created_at explicitly
        log.created_at = event_time
        session.add(log)
        result.created += 1

    session.flush()
    return result
