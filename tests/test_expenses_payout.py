"""Tests for Reimbursement Payout Review & Hardening (Wave W6)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_payout_modes_endpoint(client: TestClient) -> None:
    token = _login(client, "admin@mediatehealthcare.com", "Admin@123")
    res = client.get(
        "/api/v1/expenses/payout-modes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    modes = res.json()
    assert isinstance(modes, list)
    assert "NEFT" in modes
    assert "RTGS" in modes
    assert "UPI" in modes
    assert "CHEQUE" in modes
    assert "CASH" in modes


def test_payout_requires_admin(client: TestClient) -> None:
    # MR cannot process payout
    mr_token = _login(client, "mr@mediatehealthcare.com", "Mr@123")
    res = client.post(
        "/api/v1/expenses/1/payout",
        headers={"Authorization": f"Bearer {mr_token}"},
        json={
            "reference_no": "UTR123456789",
            "payment_mode": "NEFT",
        },
    )
    assert res.status_code == 403


def test_payout_validates_non_cash_reference(client: TestClient, db_session: Session) -> None:
    admin_token = _login(client, "admin@mediatehealthcare.com", "Admin@123")

    # 1. Create and approve an expense
    create_res = client.post(
        "/api/v1/expenses",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "expense_date": "2026-11-20",
            "expense_type": "TRAVEL_FARE",
            "amount": 500.0,
            "description": "Validation test travel",
        },
    )
    assert create_res.status_code == 201
    exp_id = create_res.json()["id"]

    from app.modules.expenses.models import Expense

    exp = db_session.query(Expense).filter(Expense.id == exp_id).first()
    assert exp is not None
    exp.status = "APPROVED"
    db_session.commit()

    # 2. Non-cash with empty reference should return 422
    res = client.post(
        f"/api/v1/expenses/{exp_id}/payout",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "reference_no": "   ",
            "payment_mode": "NEFT",
        },
    )
    assert res.status_code == 422


def test_payout_lifecycle_and_idempotency(client: TestClient, db_session: Session) -> None:
    admin_token = _login(client, "admin@mediatehealthcare.com", "Admin@123")

    # 1. Create an expense
    create_res = client.post(
        "/api/v1/expenses",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "expense_date": "2026-11-20",
            "expense_type": "TRAVEL_FARE",
            "amount": 1500.0,
            "description": "Travel from Pune to Satara",
        },
    )
    assert create_res.status_code == 201
    exp_id = create_res.json()["id"]

    # 2. Try payout on SUBMITTED expense -> should fail with 400
    payout_fail = client.post(
        f"/api/v1/expenses/{exp_id}/payout",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "reference_no": "UTR999999",
            "payment_mode": "NEFT",
        },
    )
    assert payout_fail.status_code == 400
    assert "Only APPROVED expenses" in payout_fail.text

    # 3. Simulate approve by setting status to APPROVED directly in DB
    from app.modules.expenses.models import Expense

    exp = db_session.query(Expense).filter(Expense.id == exp_id).first()
    assert exp is not None
    exp.status = "APPROVED"
    db_session.commit()

    # 4. Now process payout -> should succeed
    payout_success = client.post(
        f"/api/v1/expenses/{exp_id}/payout",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "reference_no": "UTR999999",
            "payment_mode": "NEFT",
            "idempotency_key": f"key-{exp_id}",
            "remarks": "Settle November travel",
        },
    )
    assert payout_success.status_code == 200
    data = payout_success.json()
    assert data["status"] == "PAID"

    # 5. Idempotent repeat: same call should return 200 without error or second payout
    payout_repeat = client.post(
        f"/api/v1/expenses/{exp_id}/payout",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "reference_no": "UTR999999",
            "payment_mode": "NEFT",
            "idempotency_key": f"key-{exp_id}",
        },
    )
    assert payout_repeat.status_code == 200
    assert payout_repeat.json()["status"] == "PAID"
