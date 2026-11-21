
"""Automated Endpoint Smoke Matrix for Wave W6.

Crawls every GET endpoint in the OpenAPI schema across ADMIN, MANAGER, and MR roles.
Resolves dynamic path parameters from seeded database records.
Fails with exit code 1 if any endpoint returns 500 or an unexpected status code.
"""

from __future__ import annotations

import sys
import os
import re
from pathlib import Path
from typing import Any
from fastapi.testclient import TestClient

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.db.session import SessionLocal
from app.modules.users.models import User
from app.modules.customers.models import Doctor, Chemist, Stockist
from app.modules.territories.models import Territory
from app.modules.products.models import Product
from app.modules.expenses.models import Expense
from app.modules.leaves.models import LeaveRequest
from app.modules.tours.models import TourProgram
from app.modules.tasks.models import Task
from app.modules.dashboard.metrics import metric_registry


def run_smoke_matrix() -> int:
    client = TestClient(app)
    db = SessionLocal()

    # 1. Acquire tokens for ADMIN, MANAGER, MR
    creds = {
        "ADMIN": ("admin@mediatehealthcare.com", "Admin@123"),
        "MANAGER": ("manager@mediatehealthcare.com", "Manager@123"),
        "MR": ("mr@mediatehealthcare.com", "Mr@123"),
    }
    tokens: dict[str, str] = {}
    user_ids_by_role: dict[str, int] = {}
    for role, (email, pwd) in creds.items():
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        if resp.status_code != 200:
            print(f"[FATAL] Failed to login as {role} ({email}): {resp.text}")
            return 1
        tokens[role] = resp.json()["access_token"]
        u = db.query(User).filter(User.email == email).first()
        user_ids_by_role[role] = u.id if u else 1

    task_obj = db.query(Task.id).first()
    task_id_val = task_obj[0] if task_obj else 1

    # 2. Pre-fetch sample IDs for dynamic path parameter resolution
    sample_ids: dict[str, Any] = {
        "user_id": user_ids_by_role["ADMIN"],
        "employee_id": user_ids_by_role["ADMIN"],
        "doctor_id": db.query(Doctor.id).first()[0] if db.query(Doctor.id).first() else 1,
        "chemist_id": db.query(Chemist.id).first()[0] if db.query(Chemist.id).first() else 1,
        "stockist_id": db.query(Stockist.id).first()[0] if db.query(Stockist.id).first() else 1,
        "territory_id": db.query(Territory.id).first()[0] if db.query(Territory.id).first() else 1,
        "product_id": db.query(Product.id).first()[0] if db.query(Product.id).first() else 1,
        "expense_id": db.query(Expense.id).first()[0] if db.query(Expense.id).first() else 1,
        "leave_id": db.query(LeaveRequest.id).first()[0] if db.query(LeaveRequest.id).first() else 1,
        "tour_id": db.query(TourProgram.id).first()[0] if db.query(TourProgram.id).first() else 1,
        "task_id": task_id_val,
        "id": task_id_val,
        "key": "daily_call_report",
        "metric_key": "doctor_visits",
        "type": "ATTACHMENT_TYPE",
        "source": "states",
    }

    openapi_schema = app.openapi()
    paths = openapi_schema.get("paths", {})

    # Endpoints expected to return 403 Forbidden for MR role
    admin_only_prefixes = [
        "/api/v1/users",
        "/api/v1/settings",
        "/api/v1/expenses/limits",
        "/api/v1/audit",
        "/api/v1/mappings",
        "/api/v1/mobile-registrations",
        "/api/v1/tour-plan-locks",
        "/api/v1/admin",
    ]

    total_checks = 0
    failures = 0
    results: list[tuple[str, str, str, int, str]] = []

    print("\n" + "=" * 90)
    print(f"{'METHOD':<7} | {'PATH':<48} | {'ROLE':<7} | {'STATUS':<6} | {'RESULT'}")
    print("=" * 90)

    for path, path_item in sorted(paths.items()):
        if "get" not in path_item:
            continue

        for role in ["ADMIN", "MANAGER", "MR"]:
            total_checks += 1
            headers = {"Authorization": f"Bearer {tokens[role]}"}

            # Resolve path parameters: e.g. {employee_id} -> sample_id
            resolved_path = path
            param_names = re.findall(r"\{([a-zA-Z0-9_]+)\}", path)
            skip_endpoint = False
            for p in param_names:
                if p in sample_ids:
                    resolved_path = resolved_path.replace(f"{{{p}}}", str(sample_ids[p]))
                else:
                    resolved_path = resolved_path.replace(f"{{{p}}}", "1")

            # Add default query params for lists and reports
            query_params: dict[str, Any] = {
                "page": 1,
                "page_size": 5,
                "from": "2020-01-01",
                "to": "2030-12-31",
                "month": 11,
                "year": 2026,
                "latitude": 18.5204,
                "longitude": 73.8567,
                "radius_km": 10.0,
            }

            try:
                resp = client.get(resolved_path, headers=headers, params=query_params)
                status_code = resp.status_code

                is_ok = False
                note = "OK"

                if status_code == 500:
                    failures += 1
                    note = f"FAIL (HTTP 500): {resp.text[:100]}"
                elif status_code == 404:
                    # 404 only acceptable for dynamic subresource not in seed, otherwise flag
                    if "/export" in path or "{id}" in path:
                        is_ok = True
                        note = "OK (Not seeded)"
                    else:
                        failures += 1
                        note = f"FAIL (HTTP 404): {resp.text[:100]}"
                elif status_code == 403:
                    if role in ("MR", "MANAGER") and any(path.startswith(p) for p in admin_only_prefixes):
                        is_ok = True
                        note = "OK (Forbidden as expected)"
                    elif role == "ADMIN":
                        failures += 1
                        note = f"FAIL (ADMIN got 403): {resp.text[:100]}"
                    else:
                        is_ok = True
                        note = "OK (Scoped)"
                elif 200 <= status_code < 400:
                    is_ok = True
                else:
                    failures += 1
                    note = f"FAIL (HTTP {status_code}): {resp.text[:100]}"

                results.append(("GET", resolved_path[:48], role, status_code, note))
                print(f"GET     | {resolved_path:<48} | {role:<7} | {status_code:<6} | {note}")

            except Exception as exc:
                failures += 1
                print(f"GET     | {resolved_path:<48} | {role:<7} | ERR    | EXCEPTION: {exc}")

    # 3. Visits Summary 16 Metrics Drill-down smoke test for ADMIN & MR
    for metric_key in metric_registry.get_keys():
        for role in ["ADMIN", "MR"]:
            target_id = user_ids_by_role[role]
            drill_path = f"/api/v1/dashboard/visits-summary/{target_id}/metrics/{metric_key}"
            total_checks += 1
            headers = {"Authorization": f"Bearer {tokens[role]}"}
            resp = client.get(
                drill_path,
                headers=headers,
                params={"from": "2020-01-01", "to": "2030-12-31", "page": 1, "page_size": 5},
            )
            status_code = resp.status_code
            if status_code == 200:
                note = "OK"
            else:
                failures += 1
                note = f"FAIL ({status_code}): {resp.text[:100]}"
            results.append(("GET", drill_path[:48], role, status_code, note))
            print(f"GET     | {drill_path:<48} | {role:<7} | {status_code:<6} | {note}")

    db.close()
    print("=" * 90)
    print(f"SUMMARY: Total Checks: {total_checks} | Failures: {failures}")
    if failures > 0:
        print("\nFAILED ENDPOINTS DETAILS:")
        for m, p, r, s, n in results:
            if "FAIL" in n:
                print(f"[{r:<7}] {m} {p} -> {s}: {n}")
    print("=" * 90)

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(run_smoke_matrix())
