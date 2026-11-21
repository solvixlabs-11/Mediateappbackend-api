"""Tests for Wave W5 - System Configuration, Audit Trail, and Mapping Wizard."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.audit.service import AuditService, mask_sensitive_data
from app.modules.settings.models import AppSetting, GeofenceSetting
from app.modules.settings.service import SettingsService


def get_token(client: TestClient, email: str = "admin@mediatehealthcare.com", password: str = "Admin@123") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def get_mr_token(client: TestClient) -> str:
    return get_token(client, email="mr@mediatehealthcare.com", password="Mr@123")


# 1. SETTINGS TESTS
def test_settings_groups_and_list(client: TestClient, db_session: Session) -> None:
    # Ensure test settings exist
    db_session.add(
        AppSetting(
            key="test.min_val",
            group="GPS",
            value="50",
            value_type="INTEGER",
            unit="m",
            min_value=10,
            max_value=200,
            is_provisional=True,
        )
    )
    db_session.commit()

    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/settings/groups", headers=headers)
    assert res.status_code == 200
    groups = res.json()
    assert len(groups) > 0
    gps_group = next((g for g in groups if g["group"] == "GPS"), None)
    assert gps_group is not None

    # Test single update with valid value
    update_res = client.put(
        "/api/v1/settings/test.min_val",
        headers=headers,
        json={"value": "75", "reason": "Testing update"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["value"] == "75"
    assert update_res.json()["is_provisional"] is False

    # Test validation failure (out of range)
    invalid_res = client.put(
        "/api/v1/settings/test.min_val",
        headers=headers,
        json={"value": "500"},
    )
    assert invalid_res.status_code == 422

    # Test MR user gets 403 on settings write
    mr_headers = {"Authorization": f"Bearer {get_mr_token(client)}"}
    forbidden_res = client.put(
        "/api/v1/settings/test.min_val",
        headers=mr_headers,
        json={"value": "80"},
    )
    assert forbidden_res.status_code == 403


def test_geofence_settings(client: TestClient, db_session: Session) -> None:
    db_session.add(GeofenceSetting(entity_type="DOCTOR", radius_m=200.0, min_accuracy_m=50.0))
    db_session.commit()

    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/settings/geofence", headers=headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1

    # Update geofence
    put_res = client.put(
        "/api/v1/settings/geofence",
        headers=headers,
        json={"items": [{"entity_type": "DOCTOR", "radius_m": 250.0, "min_accuracy_m": 45.0}]},
    )
    if put_res.status_code != 200:
        print("PUT GEOFENCE ERROR:", put_res.json())
    assert put_res.status_code == 200
    assert put_res.json()[0]["radius_m"] == 250.0


# 2. EXPENSE LIMITS & ENFORCEMENT
def test_expense_limits_matrix_and_enforcement(client: TestClient, db_session: Session) -> None:
    db_session.add(
        AppSetting(
            key="expense.limit_enforcement",
            group="EXPENSE",
            value="WARN",
            value_type="SELECT",
            allowed_options='["OFF", "WARN", "BLOCK"]',
        )
    )
    db_session.commit()

    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Upsert limit for MR
    upsert_res = client.put(
        "/api/v1/expense-limits/bulk",
        headers=headers,
        json={
            "items": [
                {
                    "designation_code": "MR",
                    "expense_type_code": "DAILY_ALLOWANCE",
                    "daily_limit": 300.0,
                    "monthly_limit": 5000.0,
                    "is_provisional": False,
                }
            ]
        },
    )
    assert upsert_res.status_code == 200

    # Matrix view
    mat_res = client.get("/api/v1/expense-limits/matrix", headers=headers)
    assert mat_res.status_code == 200
    matrix = mat_res.json()
    assert "designations" in matrix
    assert "expense_types" in matrix

    # Test limit enforcement in WARN mode (default)
    mr_headers = {"Authorization": f"Bearer {get_mr_token(client)}"}
    claim_warn = client.post(
        "/api/v1/expenses",
        headers=mr_headers,
        json={
            "expense_date": "2026-11-20",
            "expense_type": "DAILY_ALLOWANCE",
            "amount": 500.0,  # exceeds daily 300
            "description": "Lunch meeting",
        },
    )
    assert claim_warn.status_code == 201
    assert "LIMIT_WARN" in claim_warn.json()["description"]

    # Now set enforcement to BLOCK and verify 422
    client.put(
        "/api/v1/settings/expense.limit_enforcement",
        headers=headers,
        json={"value": "BLOCK"},
    )

    claim_block = client.post(
        "/api/v1/expenses",
        headers=mr_headers,
        json={
            "expense_date": "2026-11-20",
            "expense_type": "DAILY_ALLOWANCE",
            "amount": 500.0,
            "description": "Lunch meeting 2",
        },
    )
    assert claim_block.status_code == 422


# 3. AUDIT TRAIL & SENSITIVE MASKING
def test_audit_logs_and_masking(client: TestClient, db_session: Session) -> None:
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Record test audit event
    AuditService.record(
        db_session,
        module="TEST",
        action="CREATE",
        summary="Test audit entry with sensitive info",
        before={"password": "MySecretPassword", "phone": "9876543210", "token": "jwt-token-123"},
        after={"status": "ACTIVE"},
    )
    db_session.commit()

    res = client.get("/api/v1/audit/logs", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1

    # Check masking helper directly
    masked = mask_sensitive_data({"password": "secret", "phone": "9876543210", "token": "xyz"})
    assert masked["password"] == "******"
    assert masked["token"] == "******"
    assert masked["phone"] == "******3210"

    # MR must be forbidden from viewing audit trail (403)
    mr_headers = {"Authorization": f"Bearer {get_mr_token(client)}"}
    res_mr = client.get("/api/v1/audit/logs", headers=mr_headers)
    assert res_mr.status_code == 403


# 4. MAPPING WIZARD
def test_mapping_wizard_capabilities_and_flow(client: TestClient) -> None:
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Capabilities
    cap_res = client.get("/api/v1/mappings/capabilities", headers=headers)
    assert cap_res.status_code == 200
    assert cap_res.json()["beats"] is False
    assert "Waiting for Std Route Chart" in cap_res.json()["beats_reason"]
    assert cap_res.json()["max_items"] == 20000

    # 2. Preview
    preview_res = client.post(
        "/api/v1/mappings/preview",
        headers=headers,
        json={
            "mode": "TERRITORY",
            "target_employee_id": 1,
            "conflict_policy": "SKIP",
            "territory_ids": [],
        },
    )
    assert preview_res.status_code == 200
    batch_id = preview_res.json()["batch_id"]

    # 3. Apply
    apply_res = client.post(f"/api/v1/mappings/{batch_id}/apply", headers=headers)
    assert apply_res.status_code == 200
    assert apply_res.json()["status"] == "APPLIED"

    # 4. Revert
    revert_res = client.post(f"/api/v1/mappings/{batch_id}/revert", headers=headers)
    assert revert_res.status_code == 200
    assert revert_res.json()["status"] == "REVERTED"
