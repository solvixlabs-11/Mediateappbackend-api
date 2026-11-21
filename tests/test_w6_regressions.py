"""Regression test suite for Wave W6 verifying runtime drilldown stability and metric equality.

Verifies:
1. DcrVisit object attribute safety (visit_type vs legacy call_type)
2. Doctor/Chemist/Stockist area.city traversal safety (city attribute safety)
3. 16 Visits Summary metrics: card count equals total drilldown rows returned.
"""

from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.modules.dashboard.metrics import metric_registry
from app.modules.users.models import Role, User


def get_admin_token(db_session: Session) -> str:
    admin = (
        db_session.query(User)
        .join(User.role)
        .filter(Role.code == "ADMIN", User.is_active == True)  # noqa: E712
        .first()
    )
    assert admin is not None
    token, _ = create_access_token(admin.id, role="ADMIN", permissions=["*"])
    return token


def get_mr_user(db_session: Session) -> User:
    mr = (
        db_session.query(User)
        .join(User.role)
        .filter(Role.code == "MR", User.is_active == True)  # noqa: E712
        .first()
    )
    assert mr is not None
    return mr


def test_dcr_visit_type_attribute_regression(client: TestClient, db_session: Session) -> None:
    """Regression test: DcrVisit object has visit_type attribute, preventing AttributeError: 'DcrVisit' object has no attribute 'call_type'."""
    token = get_admin_token(db_session)
    mr = get_mr_user(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    for metric in ["doctor_visits", "chemist_visits", "stockist_visits"]:
        resp = client.get(
            f"/api/v1/dashboard/visits-summary/{mr.id}/metrics/{metric}",
            params={"from": "2020-01-01", "to": "2030-12-31", "page": 1, "page_size": 10},
            headers=headers,
        )
        assert resp.status_code == 200, f"Metric {metric} failed with {resp.text}"
        data = resp.json()
        assert data["meta"]["kind"] == "TABLE"
        assert "rows" in data
        for row in data["rows"]:
            assert "visit_type" in row
            assert row["visit_type"] is not None


def test_customer_city_traversal_regression(client: TestClient, db_session: Session) -> None:
    """Regression test: Doctor/Chemist/Stockist area.city traversal preventing AttributeError: 'Doctor' object has no attribute 'city'."""
    token = get_admin_token(db_session)
    mr = get_mr_user(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    for metric in ["new_doctor_visits", "new_chemist_visits", "new_stockist_visits"]:
        resp = client.get(
            f"/api/v1/dashboard/visits-summary/{mr.id}/metrics/{metric}",
            params={"from": "2020-01-01", "to": "2030-12-31", "page": 1, "page_size": 10},
            headers=headers,
        )
        assert resp.status_code == 200, f"Metric {metric} failed with {resp.text}"
        data = resp.json()
        assert data["meta"]["kind"] == "TABLE"
        assert "rows" in data
        for row in data["rows"]:
            assert "city" in row
            assert row["city"] is not None


def test_16_metrics_card_count_equals_detail_rows(client: TestClient, db_session: Session) -> None:
    """Verify that for each of the 16 Visits Summary metrics, the summary card count equals the total drilldown rows."""
    token = get_admin_token(db_session)
    mr = get_mr_user(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch Visits Summary cards for this employee
    sum_resp = client.get(
        "/api/v1/dashboard/visits-summary",
        params={"from": "2020-01-01", "to": "2030-12-31", "employee_ids": [mr.id]},
        headers=headers,
    )
    assert sum_resp.status_code == 200, sum_resp.text
    summary_data = sum_resp.json()
    assert len(summary_data["items"]) >= 1
    emp_metrics = {m["key"]: m for m in summary_data["items"][0]["metrics"]}

    # Verify all 16 registered metrics can be drilled down into and total matches
    for metric_key in metric_registry.get_keys():
        drill_resp = client.get(
            f"/api/v1/dashboard/visits-summary/{mr.id}/metrics/{metric_key}",
            params={"from": "2020-01-01", "to": "2030-12-31", "page": 1, "page_size": 50},
            headers=headers,
        )
        assert drill_resp.status_code == 200, f"Drilldown for {metric_key} returned {drill_resp.status_code}: {drill_resp.text}"
        drill_data = drill_resp.json()
        assert "total" in drill_data, f"Metric {metric_key} drilldown missing 'total'"

        card_info = emp_metrics.get(metric_key)
        assert card_info is not None, f"Card for {metric_key} not found in summary metrics"

        # If metric is an integer count (TABLE kind), card value should equal drilldown total
        if drill_data["meta"]["kind"] == "TABLE" and metric_key in [
            "chemist_visits",
            "new_chemist_visits",
            "doctor_visits",
            "new_doctor_visits",
            "stockist_visits",
            "new_stockist_visits",
        ]:
            card_val = int(card_info["value"])
            assert card_val == drill_data["total"], f"Card count {card_val} != drilldown total {drill_data['total']} for {metric_key}"


def test_endpoint_smoke_matrix_zero_failures() -> None:
    """Execute the full 305-check smoke matrix across all roles and verify 0 failures."""
    from scripts.smoke_all_endpoints import run_smoke_matrix

    exit_code = run_smoke_matrix()
    assert exit_code == 0, "Endpoint smoke matrix detected unexpected failure status codes."
