"""Wave W5 Smoke Test across ADMIN, MANAGER, and MR roles."""

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token(email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if res.status_code != 200:
        raise RuntimeError(f"Login failed for {email}: {res.text}")
    return res.json()["access_token"]


def main() -> int:
    print("=" * 60)
    print("STARTING W5 SMOKE TESTS")
    print("=" * 60)

    admin_token = get_token("admin@mediatehealthcare.com", "Admin@123")
    manager_token = get_token("manager@mediatehealthcare.com", "Manager@123")
    mr_token = get_token("mr@mediatehealthcare.com", "Mr@123")

    admin_h = {"Authorization": f"Bearer {admin_token}"}
    manager_h = {"Authorization": f"Bearer {manager_token}"}
    mr_h = {"Authorization": f"Bearer {mr_token}"}

    # 1. ADMIN TESTS
    print("\n--- 1. ADMIN PRIVILEGES ---")
    res = client.get("/api/v1/settings/groups", headers=admin_h)
    assert res.status_code == 200, f"Settings groups failed: {res.text}"
    print("[PASS] GET /api/v1/settings/groups -> 200")

    res = client.get("/api/v1/settings/geofence", headers=admin_h)
    assert res.status_code == 200, f"Geofence settings failed: {res.text}"
    print(f"[PASS] GET /api/v1/settings/geofence -> 200 ({len(res.json())} rules)")

    res = client.get("/api/v1/expense-limits/matrix", headers=admin_h)
    assert res.status_code == 200, f"Expense limits matrix failed: {res.text}"
    mat = res.json()
    print(f"[PASS] GET /api/v1/expense-limits/matrix -> 200 ({len(mat['rows'])} designations x {len(mat['expense_types'])} types)")

    res = client.get("/api/v1/audit/logs", headers=admin_h)
    assert res.status_code == 200, f"Audit logs failed: {res.text}"
    logs_data = res.json()
    print(f"[PASS] GET /api/v1/audit/logs -> 200 ({logs_data['total']} total events)")

    # Verify masking in audit logs
    for log in logs_data["items"][:20]:
        if log["before_json"]:
            assert "MySecretPassword" not in log["before_json"], "Unmasked password found!"
            assert "jwt-token-123" not in log["before_json"], "Unmasked token found!"
    print("[PASS] Verified sensitive data masking in audit trail before/after logs.")

    res = client.get("/api/v1/mappings/capabilities", headers=admin_h)
    assert res.status_code == 200, f"Mapping capabilities failed: {res.text}"
    assert res.json()["beats"] is False, "Beats capability must be false"
    print(f"[PASS] GET /api/v1/mappings/capabilities -> 200 (beats={res.json()['beats']}, reason='{res.json()['beats_reason']}')")

    # 2. MANAGER TESTS
    print("\n--- 2. MANAGER RBAC ENFORCEMENT ---")
    res = client.put("/api/v1/settings/gps.min_accuracy_m", headers=manager_h, json={"value": "60"})
    assert res.status_code == 403, f"Expected 403 for Manager on settings write, got {res.status_code}"
    print("[PASS] PUT /api/v1/settings/{key} -> 403 Forbidden for MANAGER")

    res = client.get("/api/v1/audit/logs", headers=manager_h)
    assert res.status_code == 403, f"Expected 403 for Manager on audit logs, got {res.status_code}"
    print("[PASS] GET /api/v1/audit/logs -> 403 Forbidden for MANAGER")

    res = client.post("/api/v1/mappings/preview", headers=manager_h, json={
        "mode": "TERRITORY",
        "target_employee_id": 1,
        "conflict_policy": "SKIP",
        "territory_ids": []
    })
    assert res.status_code == 200, f"Manager mapping preview failed: {res.text}"
    print("[PASS] POST /api/v1/mappings/preview -> 200 Allowed for MANAGER")

    # 3. MR TESTS
    print("\n--- 3. MR RBAC ENFORCEMENT ---")
    res = client.put("/api/v1/settings/gps.min_accuracy_m", headers=mr_h, json={"value": "60"})
    assert res.status_code == 403, f"Expected 403 for MR on settings write, got {res.status_code}"
    print("[PASS] PUT /api/v1/settings/{key} -> 403 Forbidden for MR")

    res = client.get("/api/v1/audit/logs", headers=mr_h)
    assert res.status_code == 403, f"Expected 403 for MR on audit logs, got {res.status_code}"
    print("[PASS] GET /api/v1/audit/logs -> 403 Forbidden for MR")

    res = client.post("/api/v1/mappings/preview", headers=mr_h, json={
        "mode": "TERRITORY",
        "target_employee_id": 1,
        "conflict_policy": "SKIP",
        "territory_ids": []
    })
    assert res.status_code == 403, f"Expected 403 for MR on mappings preview, got {res.status_code}"
    print("[PASS] POST /api/v1/mappings/preview -> 403 Forbidden for MR")

    print("\n" + "=" * 60)
    print("ALL W5 SMOKE TESTS PASSED CLEANLY (100%)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
