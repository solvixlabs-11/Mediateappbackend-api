"""Tests for Wave W8 Sample Inventory & Stock Management."""

from datetime import date, timedelta
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_admin_headers() -> dict[str, str]:
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mediatehealthcare.com", "password": "Admin@123"},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_sample_inward_lifecycle_and_balance_update():
    headers = get_admin_headers()
    today = date.today()

    # 1. Fetch available products
    prod_res = client.get("/api/v1/products?limit=5", headers=headers)
    assert prod_res.status_code == 200
    products = prod_res.json()
    assert len(products) > 0
    target_product = products[0]

    # 2. Record Inward with past expiry (must fail)
    past_inward_payload = {
        "challan_number": f"CHAL-TEST-FAIL-{uuid4().hex[:8]}",
        "inward_date": str(today),
        "product_id": target_product["id"],
        "batch_number": "BATCH-EXP",
        "expiry_date": str(today - timedelta(days=5)),
        "quantity": 100,
        "unit_cost": 15.0,
    }
    fail_res = client.post(
        "/api/v1/stock/samples/inward",
        json=past_inward_payload,
        headers=headers,
    )
    assert fail_res.status_code == 400
    assert "expiry date must be in the future" in fail_res.json()["detail"].lower()

    # 3. Record Valid Inward
    valid_challan = f"CHAL-TEST-OK-{uuid4().hex[:8].upper()}"
    valid_batch = f"BATCH-OK-{uuid4().hex[:6].upper()}"
    valid_payload = {
        "challan_number": valid_challan,
        "inward_date": str(today),
        "product_id": target_product["id"],
        "batch_number": valid_batch,
        "mfg_date": str(today - timedelta(days=30)),
        "expiry_date": str(today + timedelta(days=365)),
        "quantity": 250,
        "unit_cost": 18.5,
        "supplier_name": "Test Formulations Ltd",
        "remarks": "Pytest verified sample inward batch",
    }
    inward_res = client.post(
        "/api/v1/stock/samples/inward",
        json=valid_payload,
        headers=headers,
    )
    assert inward_res.status_code == 201
    inward_data = inward_res.json()
    assert inward_data["challan_number"] == valid_challan
    assert inward_data["quantity"] == 250

    # 4. Duplicate Challan check
    dup_res = client.post(
        "/api/v1/stock/samples/inward",
        json=valid_payload,
        headers=headers,
    )
    assert dup_res.status_code == 400
    assert "already been processed" in dup_res.json()["detail"]

    # 5. Verify batch inventory reflects in batches
    batch_res = client.get(
        f"/api/v1/stock/samples/batches?product_id={target_product['id']}",
        headers=headers,
    )
    assert batch_res.status_code == 200
    batches = batch_res.json()
    matching_batch = next((b for b in batches if b["batch_number"] == valid_batch), None)
    assert matching_batch is not None
    assert matching_batch["quantity_balance"] >= 250
    assert matching_batch["expiry_status"] == "ACTIVE"


def test_sample_allocation_single_and_bulk():
    headers = get_admin_headers()
    today = date.today()

    # Get users and products
    users_res = client.get("/api/v1/users?page_size=5", headers=headers)
    assert users_res.status_code == 200
    users = users_res.json()["items"]
    assert len(users) > 0
    target_user = users[0]

    prod_res = client.get("/api/v1/products?limit=2", headers=headers)
    target_product = prod_res.json()[0]

    # 1. Single Allocation
    alloc_payload = {
        "user_id": target_user["id"],
        "product_id": target_product["id"],
        "month": today.month,
        "year": today.year,
        "allocated_quantity": 75,
    }
    create_alloc_res = client.post(
        "/api/v1/stock/samples/allocations",
        json=alloc_payload,
        headers=headers,
    )
    assert create_alloc_res.status_code == 201
    alloc_data = create_alloc_res.json()
    assert alloc_data["allocated_quantity"] == 75

    # 2. Bulk Allocation
    bulk_payload = {
        "month": today.month,
        "year": today.year,
        "allocations": [
            {
                "user_id": target_user["id"],
                "product_id": target_product["id"],
                "allocated_quantity": 90,
            }
        ],
    }
    bulk_res = client.post(
        "/api/v1/stock/samples/allocations/bulk",
        json=bulk_payload,
        headers=headers,
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["processed_count"] == 1


def test_sample_issue_and_acknowledgment():
    headers = get_admin_headers()
    today = date.today()

    # Get batches with positive balance
    batches_res = client.get("/api/v1/stock/samples/batches", headers=headers)
    assert batches_res.status_code == 200
    batches = batches_res.json()
    available_batch = next((b for b in batches if b["quantity_balance"] >= 10), None)
    assert available_batch is not None

    users_res = client.get("/api/v1/users?page_size=5", headers=headers)
    target_user = users_res.json()["items"][0]

    # 1. Issue with excessive quantity (must fail)
    excess_payload = {
        "user_id": target_user["id"],
        "product_id": available_batch["product_id"],
        "batch_number": available_batch["batch_number"],
        "quantity": available_batch["quantity_balance"] + 1000,
        "dispatch_mode": "COURIER",
    }
    excess_res = client.post(
        "/api/v1/stock/samples/issues",
        json=excess_payload,
        headers=headers,
    )
    assert excess_res.status_code == 400
    assert "insufficient sample stock" in excess_res.json()["detail"].lower()

    # 2. Valid Issue
    issue_qty = 5
    valid_issue_payload = {
        "user_id": target_user["id"],
        "product_id": available_batch["product_id"],
        "batch_number": available_batch["batch_number"],
        "quantity": issue_qty,
        "dispatch_mode": "COURIER",
        "tracking_reference": "TEST-DOCKET-9911",
        "remarks": "Sampling kit dispatch test",
    }
    issue_res = client.post(
        "/api/v1/stock/samples/issues",
        json=valid_issue_payload,
        headers=headers,
    )
    assert issue_res.status_code == 201
    issue_data = issue_res.json()
    assert issue_data["status"] == "DISPATCHED"
    assert issue_data["quantity"] == issue_qty
    issue_id = issue_data["id"]

    # 3. Acknowledge Receipt
    ack_res = client.post(
        f"/api/v1/stock/samples/issues/{issue_id}/acknowledge",
        json={"received_date": str(today), "remarks": "Box received intact"},
        headers=headers,
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    # 4. Check Stock Balance Report Endpoint
    balance_res = client.get("/api/v1/stock/samples/balance", headers=headers)
    assert balance_res.status_code == 200
    report_items = balance_res.json()
    assert isinstance(report_items, list)
    assert len(report_items) > 0
    first_item = report_items[0]
    assert "ho_balance" in first_item
    assert "total_allocated" in first_item
    assert "total_issued" in first_item
    assert "mr_holding_balance" in first_item
