"""Test suite for Workflow Inbox endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.customers.models import Chemist, Doctor, Stockist
from app.modules.leaves.models import LeaveRequest
from app.modules.tours.models import TourProgram
from app.modules.users.models import User


def get_token(client: TestClient, email: str = "admin@mediatehealthcare.com") -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Admin@123"})
    if resp.status_code != 200:
        # Fallback to dev test account
        resp = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Password123!"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_workflow_summary_and_items_flow(client: TestClient) -> None:
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Summary for leaves
    resp = client.get("/api/v1/workflow/leaves/summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "drafts" in data
    assert "applied" in data
    assert "received" in data
    assert data["module"] == "leaves"

    # 2. List items for leaves (received box)
    resp = client.get("/api/v1/workflow/leaves?box=received", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)

    # 3. Summary for tours
    resp = client.get("/api/v1/workflow/tours/summary", headers=headers)
    assert resp.status_code == 200
    t_data = resp.json()
    assert "drafts" in t_data
    assert "received" in t_data

    # 4. Summary for new customers
    for cust in ["new-doctors", "new-chemists", "new-stockists"]:
        c_resp = client.get(f"/api/v1/workflow/{cust}/summary", headers=headers)
        assert c_resp.status_code == 200
        assert "applied" in c_resp.json()
