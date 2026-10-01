"""Tests for Approvals, Tour Programs, Expense Claims, and Leave Management."""

from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, role: str) -> str:
    """Helper to acquire JWT bearer token for role."""
    creds = {
        "admin": ("admin@mediatehealthcare.com", "Admin@123"),
        "manager": ("manager@mediatehealthcare.com", "Manager@123"),
        "mr": ("mr@mediatehealthcare.com", "Mr@123"),
    }
    email, password = creds[role]
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_tour_program_and_approval_flow(client: TestClient) -> None:
    """Test Tour creation, BR-09 overlap rejection, and manager approval."""
    mr_token = get_auth_token(client, "mr")
    mgr_token = get_auth_token(client, "manager")

    start = dt.date.today() + dt.timedelta(days=10)
    end = start + dt.timedelta(days=5)

    # 1. MR creates Tour Program
    resp = client.post(
        "/api/v1/tours",
        headers={"Authorization": f"Bearer {mr_token}"},
        json={
            "title": "North Zone Doctor Tour",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "route_details": "Delhi - Chandigarh - Shimla",
            "objectives": "Meet top cardiologists",
        },
    )
    assert resp.status_code == 201, resp.text
    tour_data = resp.json()
    assert tour_data["status"] == "SUBMITTED"
    assert tour_data["total_days"] == 6
    assert tour_data["approval_request_id"] is not None

    app_id = tour_data["approval_request_id"]

    # 2. BR-09: Overlapping tour must be rejected with 409
    overlap_resp = client.post(
        "/api/v1/tours",
        headers={"Authorization": f"Bearer {mr_token}"},
        json={
            "title": "Conflicting Tour",
            "start_date": (start + dt.timedelta(days=2)).isoformat(),
            "end_date": (end + dt.timedelta(days=2)).isoformat(),
        },
    )
    assert overlap_resp.status_code == 409, overlap_resp.text

    # 3. Manager views inbox
    inbox_resp = client.get(
        "/api/v1/approvals/inbox",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert inbox_resp.status_code == 200, inbox_resp.text
    items = inbox_resp.json()
    assert any(i["id"] == app_id for i in items)

    # 4. Manager approves the Tour
    dec_resp = client.post(
        f"/api/v1/approvals/{app_id}/decision",
        headers={"Authorization": f"Bearer {mgr_token}"},
        json={"decision": "APPROVED", "comments": "Tour approved. Good luck."},
    )
    assert dec_resp.status_code == 200, dec_resp.text
    assert dec_resp.json()["status"] == "APPROVED"

    # Verify Tour status is now APPROVED
    t_check = client.get(
        f"/api/v1/tours/{tour_data['id']}",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert t_check.status_code == 200
    assert t_check.json()["status"] == "APPROVED"


def test_expense_claims_and_summary_flow(client: TestClient) -> None:
    """Test expense claim entry, manager rejection with comment (BR-08), and monthly summary."""
    mr_token = get_auth_token(client, "mr")
    mgr_token = get_auth_token(client, "manager")

    today = dt.date.today()

    # 1. MR submits Expense
    resp = client.post(
        "/api/v1/expenses",
        headers={"Authorization": f"Bearer {mr_token}"},
        json={
            "expense_date": today.isoformat(),
            "expense_type": "TRAVEL_FARE",
            "amount": 1250.00,
            "description": "Taxi from HQ to Hospital cluster",
            "client_uuid": "exp-uuid-test-001",
        },
    )
    assert resp.status_code == 201, resp.text
    exp_data = resp.json()
    assert exp_data["status"] == "SUBMITTED"
    assert exp_data["amount"] == 1250.00

    app_id = exp_data["approval_request_id"]

    # 2. BR-08: Rejection without comment should fail with 422
    rej_fail = client.post(
        f"/api/v1/approvals/{app_id}/decision",
        headers={"Authorization": f"Bearer {mgr_token}"},
        json={"decision": "REJECTED", "comments": None},
    )
    assert rej_fail.status_code == 422, rej_fail.text

    # 3. Manager rejects with comment
    rej_ok = client.post(
        f"/api/v1/approvals/{app_id}/decision",
        headers={"Authorization": f"Bearer {mgr_token}"},
        json={"decision": "REJECTED", "comments": "Receipt bill missing."},
    )
    assert rej_ok.status_code == 200, rej_ok.text
    assert rej_ok.json()["status"] == "REJECTED"

    # 4. Check monthly summary
    sum_resp = client.get(
        "/api/v1/expenses/summary",
        headers={"Authorization": f"Bearer {mr_token}"},
        params={"year": today.year, "month": today.month},
    )
    assert sum_resp.status_code == 200, sum_resp.text
    summary = sum_resp.json()
    assert summary["total_rejected"] >= 1250.00


def test_leave_management_and_balance_rules(client: TestClient) -> None:
    """Test Leave application, balance deduction on approval (BR-10), and restoration on cancel."""
    mr_token = get_auth_token(client, "mr")
    mgr_token = get_auth_token(client, "manager")

    start = dt.date.today() + dt.timedelta(days=30)
    end = start + dt.timedelta(days=1)

    # 1. Check initial balances
    bal_resp = client.get(
        "/api/v1/leaves/balances",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert bal_resp.status_code == 200, bal_resp.text
    initial_casual = bal_resp.json()["casual_leave_balance"]

    # 2. MR applies for Casual Leave
    apply_resp = client.post(
        "/api/v1/leaves",
        headers={"Authorization": f"Bearer {mr_token}"},
        json={
            "leave_type": "CASUAL",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "days_count": 2.0,
            "reason": "Family event",
            "client_uuid": "leave-uuid-test-001",
        },
    )
    assert apply_resp.status_code == 201, apply_resp.text
    leave_data = apply_resp.json()
    assert leave_data["status"] == "PENDING"
    app_id = leave_data["approval_request_id"]

    # 3. Manager approves leave
    appr_resp = client.post(
        f"/api/v1/approvals/{app_id}/decision",
        headers={"Authorization": f"Bearer {mgr_token}"},
        json={"decision": "APPROVED", "comments": "Approved. Have a good time."},
    )
    assert appr_resp.status_code == 200, appr_resp.text

    # 4. Verify balance is deducted by 2 days (BR-10)
    bal_after = client.get(
        "/api/v1/leaves/balances",
        headers={"Authorization": f"Bearer {mr_token}"},
    ).json()
    assert bal_after["casual_leave_balance"] == initial_casual - 2.0

    # 5. Cancel leave and verify balance restored (BR-10)
    cancel_resp = client.post(
        f"/api/v1/leaves/{leave_data['id']}/cancel",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert cancel_resp.status_code == 200, cancel_resp.text
    assert cancel_resp.json()["status"] == "CANCELLED"

    bal_restored = client.get(
        "/api/v1/leaves/balances",
        headers={"Authorization": f"Bearer {mr_token}"},
    ).json()
    assert bal_restored["casual_leave_balance"] == initial_casual
