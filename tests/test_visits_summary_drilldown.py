"""Integration & Unit tests for Visits Summary Drill-Down (Contract & Logic)."""

import io
from datetime import date
import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.modules.dashboard.metrics import metric_registry
from app.modules.users.models import Role, User


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def admin_token(db_session):
    admin = (
        db_session.query(User)
        .join(User.role)
        .filter(Role.code == "ADMIN", User.is_active == True)  # noqa: E712
        .first()
    )
    assert admin is not None
    token, _ = create_access_token(admin.id, role="ADMIN", permissions=["*"])
    return token


@pytest.fixture(scope="module")
def mr_user(db_session):
    mr = (
        db_session.query(User)
        .join(User.role)
        .filter(Role.code == "MR", User.is_active == True)  # noqa: E712
        .first()
    )
    assert mr is not None
    return mr


@pytest.fixture(scope="module")
def mr_token(mr_user):
    token, _ = create_access_token(mr_user.id, role="MR", permissions=["dashboard:read"])
    return token


def test_metric_registry_contains_16_metrics():
    """Verify registry loads all 16 canonical metrics."""
    keys = metric_registry.get_keys()
    assert len(keys) == 16
    expected = [
        "chemist_visits",
        "new_chemist_visits",
        "doctor_visits",
        "new_doctor_visits",
        "stockist_visits",
        "new_stockist_visits",
        "doctor_call_average",
        "missing_doctor",
        "punch_in_time",
        "first_call_time",
        "last_call_time",
        "punch_out_time",
        "morning_calls",
        "evening_calls",
        "work_duration",
        "total_pob",
    ]
    for k in expected:
        assert k in keys
        handler = metric_registry.get(k)
        assert handler is not None
        assert handler.key == k


def test_visits_summary_returns_dynamic_metrics(client, admin_token, mr_user):
    """Verify /visits-summary response contains dynamic metrics list for each employee."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get(
        "/api/v1/dashboard/visits-summary",
        params={"from": str(date.today()), "to": str(date.today()), "employee_ids": [mr_user.id]},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    emp = data["items"][0]
    assert "metrics" in emp
    assert len(emp["metrics"]) == 16

    # Verify metric keys present
    metric_keys = [m["key"] for m in emp["metrics"]]
    assert "chemist_visits" in metric_keys
    assert "doctor_call_average" in metric_keys
    assert "total_pob" in metric_keys

    # Verify colors
    color_map = {m["key"]: m["color_group"] for m in emp["metrics"]}
    assert color_map["doctor_visits"] == "primary"
    assert color_map["doctor_call_average"] == "success"
    assert color_map["missing_doctor"] == "success"
    assert color_map["total_pob"] == "danger"


def test_metric_drilldown_table_metrics(client, admin_token, mr_user):
    """Verify TABLE kind metric drilldown returns correct schema, meta, and rows."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    for metric_key in ["chemist_visits", "doctor_visits", "stockist_visits"]:
        res = client.get(
            f"/api/v1/dashboard/visits-summary/{mr_user.id}/metrics/{metric_key}",
            params={"from": "2020-01-01", "to": "2030-12-31", "page": 1, "page_size": 10},
            headers=headers,
        )
        assert res.status_code == 200, f"Failed for {metric_key}: {res.text}"
        data = res.json()
        assert data["meta"]["kind"] == "TABLE"
        assert len(data["meta"]["columns"]) > 0
        assert "rows" in data
        assert data["total"] == len(data["rows"]) or data["total"] >= len(data["rows"])


def test_metric_drilldown_record_metrics(client, admin_token, mr_user):
    """Verify RECORD kind metric drilldown returns record object with fields & map pin."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    for metric_key in ["punch_in_time", "first_call_time", "last_call_time", "punch_out_time"]:
        res = client.get(
            f"/api/v1/dashboard/visits-summary/{mr_user.id}/metrics/{metric_key}",
            params={"from": "2020-01-01", "to": "2030-12-31"},
            headers=headers,
        )
        assert res.status_code == 200, f"Failed for {metric_key}: {res.text}"
        data = res.json()
        assert data["meta"]["kind"] == "RECORD"
        assert "record" in data
        assert "fields" in data["record"]


def test_metric_drilldown_timeline_metric(client, admin_token, mr_user):
    """Verify TIMELINE kind metric drilldown returns events array."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get(
        f"/api/v1/dashboard/visits-summary/{mr_user.id}/metrics/work_duration",
        params={"from": "2020-01-01", "to": "2030-12-31"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["meta"]["kind"] == "TIMELINE"
    assert "events" in data


def test_total_pob_coming_soon(client, admin_token, mr_user):
    """Verify total_pob returns status COMING_SOON and no fake rows."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get(
        f"/api/v1/dashboard/visits-summary/{mr_user.id}/metrics/total_pob",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["meta"]["status"] == "COMING_SOON"
    assert data["meta"]["unavailable_reason"] is not None
    assert len(data["rows"]) == 0
    assert data["total"] == 0


def test_scope_enforcement(client, mr_token, mr_user, db_session):
    """Verify MR can access own metrics but is DENIED for other employees."""
    # Find another MR user
    other_mr = (
        db_session.query(User)
        .join(User.role)
        .filter(Role.code == "MR", User.id != mr_user.id, User.is_active == True)  # noqa: E712
        .first()
    )
    assert other_mr is not None

    headers = {"Authorization": f"Bearer {mr_token}"}

    # Own metrics should succeed
    res_own = client.get(
        f"/api/v1/dashboard/visits-summary/{mr_user.id}/metrics/doctor_visits",
        headers=headers,
    )
    assert res_own.status_code == 200

    # Other employee metrics should return 403 REPORT_SCOPE_DENIED
    res_other = client.get(
        f"/api/v1/dashboard/visits-summary/{other_mr.id}/metrics/doctor_visits",
        headers=headers,
    )
    assert res_other.status_code == 403
    assert "REPORT_SCOPE_DENIED" in res_other.json()["detail"]


def test_excel_export_metric(client, admin_token, mr_user):
    """Verify Excel export produces valid .xlsx spreadsheet."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get(
        f"/api/v1/dashboard/visits-summary/{mr_user.id}/metrics/doctor_visits/export?format=xlsx",
        params={"from": "2020-01-01", "to": "2030-12-31"},
        headers=headers,
    )
    assert res.status_code == 200
    assert "spreadsheetml.sheet" in res.headers["content-type"]
    assert res.content[:2] == b"PK"  # Zip/XLSX magic bytes

    # Verify openpyxl can read it
    wb = openpyxl.load_workbook(io.BytesIO(res.content))
    assert len(wb.sheetnames) >= 1

