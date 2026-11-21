"""Tests for Wave W9: Financial Years & App Releases (What's New)."""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_auth_token(email: str = "admin@mediatehealthcare.com", password: str = "Admin@123") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


def test_financial_years_lifecycle():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List financial years
    res = client.get("/api/v1/financial-years", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert data["total"] >= 3

    # 2. Get current financial year
    res_current = client.get("/api/v1/financial-years/current", headers=headers)
    assert res_current.status_code == 200, res_current.text
    curr_data = res_current.json()
    assert curr_data is not None
    assert curr_data["is_current"] is True

    # 3. Create new financial year
    fy_code = "2028-2029"
    create_payload = {
        "name": "FY 2028-2029",
        "code": fy_code,
        "start_date": "2028-04-01",
        "end_date": "2029-03-31",
        "is_current": False,
        "is_active": True,
        "description": "Forward outlook fiscal period",
    }
    res_create = client.post("/api/v1/financial-years", headers=headers, json=create_payload)
    if res_create.status_code == 400 and "already exists" in res_create.text:
        # Already created in a prior test run
        pass
    else:
        assert res_create.status_code == 201, res_create.text
        created_fy = res_create.json()
        assert created_fy["code"] == fy_code
        fy_id = created_fy["id"]

        # 4. Set as current
        res_set = client.post(f"/api/v1/financial-years/{fy_id}/set-current", headers=headers)
        assert res_set.status_code == 200, res_set.text
        assert res_set.json()["is_current"] is True

        # Verify old current is unset
        res_new_curr = client.get("/api/v1/financial-years/current", headers=headers)
        assert res_new_curr.status_code == 200
        assert res_new_curr.json()["id"] == fy_id

    # 5. Invalid date validation (start >= end)
    res_invalid = client.post(
        "/api/v1/financial-years",
        headers=headers,
        json={
            "name": "Invalid FY",
            "code": "INVALID-FY",
            "start_date": "2028-04-01",
            "end_date": "2027-03-31",
            "is_current": False,
            "is_active": True,
        },
    )
    assert res_invalid.status_code == 422


def test_app_releases_lifecycle():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List releases
    res = client.get("/api/v1/releases", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert data["total"] >= 3

    # 2. Get latest release
    res_latest = client.get("/api/v1/releases/latest", headers=headers)
    assert res_latest.status_code == 200, res_latest.text
    latest = res_latest.json()
    assert latest is not None
    assert "version" in latest

    # 3. Create new release
    rel_payload = {
        "version": "v2.3.0-TEST",
        "title": "Corporate Fiscal Governance & What's New Releases",
        "release_date": "2026-11-22",
        "release_type": "WEB_UPDATE",
        "summary": "Introduced Financial Year master and in-app system changelog engine.",
        "highlights": [
            "Corporate fiscal year administration",
            "Live in-app changelogs and mobile release updates",
        ],
        "target_audience": "ALL",
        "is_published": True,
    }
    res_create = client.post("/api/v1/releases", headers=headers, json=rel_payload)
    assert res_create.status_code == 201, res_create.text
    created = res_create.json()
    assert created["version"] == "v2.3.0-TEST"
    assert len(created["highlights"]) == 2

    # 4. Update release
    res_update = client.put(
        f"/api/v1/releases/{created['id']}",
        headers=headers,
        json={"title": "Updated Title for v2.3.0-TEST"},
    )
    assert res_update.status_code == 200, res_update.text
    assert res_update.json()["title"] == "Updated Title for v2.3.0-TEST"
