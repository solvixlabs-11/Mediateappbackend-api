"""Tests for Wave W6 Features: Provisional Masters, Company Profile, Meetings, and Calendar."""

import pytest
from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_provisional_masters_and_confirm(client: TestClient) -> None:
    token = _login(client, "admin@mediatehealthcare.com", "Admin@123")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch attachment types - should have provisional items
    res = client.get("/api/v1/masters?type=ATTACHMENT_TYPE", headers=headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0

    first_item = items[0]
    item_id = first_item["id"]

    # 2. Confirm single provisional item
    conf_res = client.post(
        f"/api/v1/masters/ATTACHMENT_TYPE/{item_id}/confirm",
        headers=headers,
    )
    assert conf_res.status_code == 200
    assert conf_res.json()["is_provisional"] is False

    # 3. Bulk confirm remaining items
    remaining_ids = [it["id"] for it in items[1:]]
    if remaining_ids:
        bulk_res = client.post(
            "/api/v1/masters/ATTACHMENT_TYPE/confirm-bulk",
            headers=headers,
            json={"item_ids": remaining_ids},
        )
        assert bulk_res.status_code == 200
        for it in bulk_res.json():
            assert it["is_provisional"] is False


def test_company_profile_and_auth_branding(client: TestClient) -> None:
    token = _login(client, "admin@mediatehealthcare.com", "Admin@123")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET company-profile
    res = client.get("/api/v1/company-profile", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "company_name" in data
    assert "company_code" in data

    # 2. PUT company-profile
    update_res = client.put(
        "/api/v1/company-profile",
        headers=headers,
        json={
            "company_name": "Mediate Field Operations Ltd.",
            "company_code": "MED-OPS",
            "city": "Pune",
            "state": "Maharashtra",
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["company_name"] == "Mediate Field Operations Ltd."
    assert update_res.json()["company_code"] == "MED-OPS"

    # 3. GET auth/config should reflect updated branding
    auth_cfg = client.get("/api/v1/auth/config")
    assert auth_cfg.status_code == 200
    cfg_data = auth_cfg.json()
    assert cfg_data["company_name"] == "Mediate Field Operations Ltd."
    assert cfg_data["company_code"] == "MED-OPS"


def test_meetings_workflow(client: TestClient) -> None:
    admin_token = _login(client, "admin@mediatehealthcare.com", "Admin@123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. GET meetings summary
    summary_res = client.get("/api/v1/meetings/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert "drafts" in summary
    assert "applied" in summary
    assert "received" in summary
    assert "total" in summary

    # 2. Create new meeting draft
    create_res = client.post(
        "/api/v1/meetings",
        headers=headers,
        json={
            "agenda": "Test Workflow Meeting 2026",
            "meeting_type": "CYCLE_MEETING",
            "start_date": "2026-12-01T10:00:00",
            "end_date": "2026-12-01T12:00:00",
            "status": "DRAFT",
        },
    )
    assert create_res.status_code == 201
    m_id = create_res.json()["id"]

    # 3. Submit meeting (DRAFT -> APPLIED)
    sub_res = client.post(f"/api/v1/meetings/{m_id}/submit", headers=headers)
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "APPLIED"

    # 4. Approve meeting (APPLIED -> APPROVED)
    app_res = client.post(
        f"/api/v1/meetings/{m_id}/approve?remarks=Approved+by+management",
        headers=headers,
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"


def test_calendar_month_endpoint(client: TestClient) -> None:
    token = _login(client, "admin@mediatehealthcare.com", "Admin@123")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(
        "/api/v1/calendar/month?year=2026&month=11",
        headers=headers,
    )
    assert res.status_code == 200
    cal_data = res.json()
    assert cal_data["year"] == 2026
    assert cal_data["month"] == 11
    assert len(cal_data["days"]) == 30  # November has 30 days
    assert "monthly_totals" in cal_data

    # Every day should have counts structure
    for day in cal_data["days"]:
        assert "doctor" in day["counts"]
        assert "chemist" in day["counts"]
        assert "stockist" in day["counts"]
        assert "new_doctor" in day["counts"]
        assert "events" in day
