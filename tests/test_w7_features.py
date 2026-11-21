"""Test suite for Wave W7 backend features.

Features tested:
1. Mobile Registrations: list, bulk approve, bulk reject, device binding & account activation.
2. Delete My Visits: preview token, atomic soft-delete, side-effect rollbacks (planned visits & follow-ups), restore window.
3. Tour Plan Lock: cutoff enforcement, scope checks, admin override, lock & unlock lifecycle.
"""

from datetime import UTC, date, datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.dcr.models import DcrVisit, FollowUp, PlannedVisit
from app.modules.mobile_registrations.models import MobileRegistration
from app.modules.tours.models import TourPlanLock, TourProgram
from app.modules.users.models import Role, User


def get_token(client: TestClient, email: str = "admin@mediatehealthcare.com", password: str = "Admin@123") -> str:
    """Helper to authenticate and return access token."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_mobile_registrations_lifecycle(client: TestClient, db_session: Session) -> None:
    """Test list, bulk approve, and bulk reject for mobile registrations."""
    admin_token = get_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create a dummy employee and a registration
    role = db_session.query(Role).filter(Role.code == "MR").first()
    test_user = User(
        email="device.test@mediate.com",
        hashed_password="hash",
        full_name="Device Test Rep",
        role_id=role.id,
        is_active=False,  # inactive until approved
    )
    db_session.add(test_user)
    db_session.flush()

    reg1 = MobileRegistration(
        registration_code="REG-TEST-001",
        employee_id=test_user.id,
        device_id_hash="hash-12345",
        device_model="Samsung S23",
        status="PENDING",
        requested_at=datetime.now(UTC),
    )
    reg2 = MobileRegistration(
        registration_code="REG-TEST-002",
        employee_id=test_user.id,
        device_id_hash="hash-67890",
        device_model="Xiaomi Note 12",
        status="PENDING",
        requested_at=datetime.now(UTC),
    )
    db_session.add_all([reg1, reg2])
    db_session.commit()

    # 2. List registrations
    res = client.get("/api/v1/mobile-registrations?status=PENDING", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["pending_count"] >= 2
    reg_ids = [r["id"] for r in data["items"]]
    assert reg1.id in reg_ids
    assert reg2.id in reg_ids

    # 3. Approve reg1 -> employee should be activated
    approve_res = client.post(
        "/api/v1/mobile-registrations/approve",
        json={"ids": [reg1.id], "comment": "Approved test rep phone"},
        headers=headers,
    )
    assert approve_res.status_code == 200
    app_data = approve_res.json()
    assert app_data["success_count"] == 1
    assert app_data["results"][0]["status"] == "APPROVED"

    db_session.refresh(test_user)
    assert test_user.is_active is True

    # 4. Reject reg2
    reject_res = client.post(
        "/api/v1/mobile-registrations/reject",
        json={"ids": [reg2.id], "comment": "Device unauthorized"},
        headers=headers,
    )
    assert reject_res.status_code == 200
    rej_data = reject_res.json()
    assert rej_data["success_count"] == 1
    assert rej_data["results"][0]["status"] == "REJECTED"


def test_delete_my_visits_with_side_effects_and_restore(client: TestClient, db_session: Session) -> None:
    """Test preview token, soft-delete with rollback of planned visit & follow-up, and restore."""
    admin_token = get_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    user = db_session.query(User).filter(User.email == "admin@mediatehealthcare.com").first()

    # Create linked PlannedVisit, DcrVisit, and FollowUp
    planned = PlannedVisit(
        user_id=user.id,
        plan_date=date(2026, 11, 20),
        customer_type="DOCTOR",
        status="COMPLETED",
    )
    db_session.add(planned)
    db_session.flush()

    visit = DcrVisit(
        user_id=user.id,
        dcr_date=date(2026, 11, 20),
        customer_type="DOCTOR",
        planned_visit_id=planned.id,
        status="SUBMITTED",
        pob_amount=1500.0,
    )
    db_session.add(visit)
    db_session.flush()

    follow_up = FollowUp(
        user_id=user.id,
        customer_type="DOCTOR",
        dcr_visit_id=visit.id,
        due_date=date(2026, 11, 25),
        title="Collect order payment",
        status="PENDING",
    )
    db_session.add(follow_up)
    db_session.commit()

    # 1. Preview deletion
    prev_res = client.post(
        "/api/v1/admin/visits/delete-preview",
        json={"employee_ids": [user.id], "start_date": "2026-11-19", "end_date": "2026-11-21"},
        headers=headers,
    )
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["total_matching_visits"] >= 1
    token = prev_data["preview_token"]
    assert token.startswith("PV-")

    # 2. Execute deletion
    del_res = client.post(
        "/api/v1/admin/visits/delete",
        json={"preview_token": token, "reason": "Test accidental double entry clean-up"},
        headers=headers,
    )
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["deleted_count"] >= 1
    assert del_data["planned_visits_reverted"] >= 1
    assert del_data["follow_ups_cancelled"] >= 1

    # Verify database state after soft delete
    db_session.refresh(visit)
    db_session.refresh(planned)
    db_session.refresh(follow_up)
    assert visit.deleted_at is not None
    assert visit.deletion_token == token
    assert planned.status == "PLANNED"  # Reverted back
    assert follow_up.status == "CANCELLED"  # Cancelled

    # 3. Token reuse should fail
    repeat_res = client.post(
        "/api/v1/admin/visits/delete",
        json={"preview_token": token, "reason": "Repeat delete"},
        headers=headers,
    )
    assert repeat_res.status_code == 400

    # 4. Restore visits
    restore_res = client.post(
        "/api/v1/admin/visits/restore",
        json={"deletion_token": token, "reason": "Accidental deletion restored"},
        headers=headers,
    )
    assert restore_res.status_code == 200
    rest_data = restore_res.json()
    assert rest_data["restored_count"] >= 1

    db_session.refresh(visit)
    db_session.refresh(planned)
    db_session.refresh(follow_up)
    assert visit.deleted_at is None
    assert planned.status == "COMPLETED"
    assert follow_up.status == "PENDING"


def test_tour_plan_lock_enforcement_and_admin_override(client: TestClient, db_session: Session) -> None:
    """Test cutoff lock enforcement on tour creation and admin override."""
    admin_token = get_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Lock month 8 (August 2027)
    lock_res = client.post(
        "/api/v1/tour-plan-locks",
        json={
            "scope": "ALL",
            "month": 8,
            "year": 2027,
            "financial_year": "2027-2028",
            "cutoff_date": "2027-07-25",
            "reason": "August cycle tour deadline lock",
        },
        headers=headers,
    )
    assert lock_res.status_code == 201
    lock_id = lock_res.json()["id"]

    # 1. Attempt to create tour without override in locked month -> 400 TOUR_PLAN_LOCKED
    tour_payload = {
        "title": "August Field Tour",
        "start_date": "2027-08-01",
        "end_date": "2027-08-05",
        "route_details": "Mumbai - Pune Highway",
        "objectives": "Product sampling & doctor meetings",
    }
    fail_res = client.post("/api/v1/tours", json=tour_payload, headers=headers)
    assert fail_res.status_code == 400
    assert "TOUR_PLAN_LOCKED" in fail_res.json()["detail"]

    # 2. Admin override with valid reason -> 201 Created
    override_payload = {
        **tour_payload,
        "admin_override_reason": "Emergency territory re-alignment authorized by VP Sales",
    }
    ok_res = client.post("/api/v1/tours", json=override_payload, headers=headers)
    assert ok_res.status_code == 201
    assert ok_res.json()["title"] == "August Field Tour"

    # 3. Unlock lock
    unlock_res = client.post(
        f"/api/v1/tour-plan-locks/{lock_id}/unlock",
        json={"reason": "Unlocked for extended cycle planning"},
        headers=headers,
    )
    assert unlock_res.status_code == 200
    assert unlock_res.json()["status"] == "UNLOCKED"
