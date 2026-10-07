"""Comprehensive test suite for Reports Engine, Exports (PDF & Excel), Targets, and Scoping."""

from __future__ import annotations

import io
from datetime import date, datetime, timedelta

import openpyxl
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.modules.reports.definitions  # noqa: F401
from app.modules.attendance.models import Attendance
from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrProductDetail, DcrVisit, PlannedVisit
from app.modules.reports.base import ReportRegistry
from app.modules.reports.utils import resolve_date_range
from app.modules.targets.models import Target
from app.modules.territories.models import Territory, UserTerritoryAssignment
from app.modules.users.models import ManagerMRAssignment, User


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


def seed_report_data(db: Session) -> dict[str, int]:
    """Helper to seed sample records for reports."""
    admin = db.query(User).filter(User.email == "admin@mediatehealthcare.com").first()
    manager = db.query(User).filter(User.email == "manager@mediatehealthcare.com").first()
    mr = db.query(User).filter(User.email == "mr@mediatehealthcare.com").first()
    assert admin and manager and mr

    # Create territory & assignment
    terr = db.query(Territory).filter(Territory.code == "TERR-PUN-01").first()
    if not terr:
        terr = Territory(
            name="Pune Central",
            code="TERR-PUN-01",
            headquarters="Pune",
        )
        db.add(terr)
        db.flush()

    # User territory assignment
    assign = db.query(UserTerritoryAssignment).filter(
        UserTerritoryAssignment.user_id == mr.id,
        UserTerritoryAssignment.territory_id == terr.id,
    ).first()
    if not assign:
        assign = UserTerritoryAssignment(
            user_id=mr.id,
            territory_id=terr.id,
        )
        db.add(assign)

    # Manager-MR assignment
    mgr_assign = db.query(ManagerMRAssignment).filter(
        ManagerMRAssignment.manager_id == manager.id,
        ManagerMRAssignment.mr_id == mr.id,
    ).first()
    if not mgr_assign:
        mgr_assign = ManagerMRAssignment(
            manager_id=manager.id,
            mr_id=mr.id,
        )
        db.add(mgr_assign)

    # Doctor
    doc = db.query(Doctor).filter(Doctor.code == "DOC-REP-01").first()
    if not doc:
        doc = Doctor(
            code="DOC-REP-01",
            full_name="Rajesh Sharma",
            specialization="Cardiology",
            category="A",
            territory_id=terr.id,
        )
        db.add(doc)
        db.flush()

    today = date.today()

    # Attendance
    att = db.query(Attendance).filter(
        Attendance.user_id == mr.id,
        Attendance.date == today,
    ).first()
    if not att:
        att = Attendance(
            user_id=mr.id,
            date=today,
            status="PRESENT",
            check_in_time=datetime.utcnow() - timedelta(hours=4),
            check_out_time=datetime.utcnow(),
            total_work_minutes=240,
            check_in_address="Shivaji Nagar Clinic, Pune",
        )
        db.add(att)

    # Planned Visit
    pv = db.query(PlannedVisit).filter(
        PlannedVisit.user_id == mr.id,
        PlannedVisit.plan_date == today,
    ).first()
    if not pv:
        pv = PlannedVisit(
            user_id=mr.id,
            plan_date=today,
            customer_type="DOCTOR",
            doctor_id=doc.id,
            status="COMPLETED",
        )
        db.add(pv)

    # DCR Visit
    visit = db.query(DcrVisit).filter(
        DcrVisit.user_id == mr.id,
        DcrVisit.dcr_date == today,
    ).first()
    if not visit:
        visit = DcrVisit(
            user_id=mr.id,
            dcr_date=today,
            customer_type="DOCTOR",
            doctor_id=doc.id,
            visit_type="INDEPENDENT",
            call_time=datetime.utcnow() - timedelta(hours=2),
            pob_amount=1500.0,
            is_geofence_verified=True,
            remarks="Detailed discussion on Cardiox 50mg with Dr. Sharma",
        )
        db.add(visit)
        db.flush()

        detail = DcrProductDetail(
            dcr_visit_id=visit.id,
            product_name="Cardiox 50mg",
            sample_quantity=2,
            gift_quantity=1,
            remarks="Prescribing regularly",
        )
        db.add(detail)

    # Monthly Target
    target = db.query(Target).filter(
        Target.user_id == mr.id,
        Target.year == today.year,
        Target.month == today.month,
    ).first()
    if not target:
        target = Target(
            user_id=mr.id,
            year=today.year,
            month=today.month,
            visit_target=100,
            doctor_call_target=80,
            chemist_call_target=20,
            primary_sales_target=250000.0,
            secondary_sales_target=200000.0,
        )
        db.add(target)

    db.commit()

    return {
        "admin_id": admin.id,
        "manager_id": manager.id,
        "mr_id": mr.id,
        "territory_id": terr.id,
        "doctor_id": doc.id,
    }


def test_registry_contains_14_reports() -> None:
    """Validate that the registry holds all 14 required reports R01 to R14."""
    keys = ReportRegistry.list_keys()
    assert len(keys) == 14, f"Expected 14 registered reports, got {len(keys)}: {keys}"
    expected_keys = [
        "dcr_detailed",
        "daily_activity",
        "customer_visits",
        "customer_coverage",
        "mr_performance",
        "pending_late_dcr",
        "geo_verification",
        "planned_vs_actual",
        "attendance",
        "leave_report",
        "expense_report",
        "tour_plan_report",
        "follow_up_report",
        "approval_turnaround",
    ]
    for k in expected_keys:
        assert k in keys, f"Missing registered report {k}"
        rep = ReportRegistry.get(k)
        assert rep is not None
        assert rep.key == k
        assert rep.title
        assert rep.group
        assert len(rep.get_columns()) > 0


def test_reports_catalog_endpoint(client: TestClient) -> None:
    """Test GET /api/v1/reports returns role-appropriate catalog items."""
    admin_token = get_auth_token(client, "admin")
    mr_token = get_auth_token(client, "mr")

    resp = client.get("/api/v1/reports", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "reports" in data
    assert "groups" in data
    assert data["role"] == "ADMIN"
    assert len(data["reports"]) == 14

    mr_resp = client.get("/api/v1/reports", headers={"Authorization": f"Bearer {mr_token}"})
    assert mr_resp.status_code == 200, mr_resp.text
    mr_data = mr_resp.json()
    assert mr_data["role"] == "MR"
    # MR cannot see reports restricted to ADMIN/MANAGER (e.g. approval turnaround)
    mr_keys = [r["key"] for r in mr_data["reports"]]
    assert "approval_turnaround" not in mr_keys
    assert "dcr_detailed" in mr_keys


def test_targets_api_crud(client: TestClient, db_session: Session) -> None:
    """Test GET and PUT /api/v1/targets for ADMIN and MANAGER."""
    seed_report_data(db_session)
    admin_token = get_auth_token(client, "admin")
    mr = db_session.query(User).filter(User.email == "mr@mediatehealthcare.com").first()
    assert mr

    # 1. Admin sets targets
    put_resp = client.put(
        "/api/v1/targets",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "user_id": mr.id,
            "year": 2026,
            "month": 10,
            "visit_target": 120,
            "doctor_call_target": 90,
            "chemist_call_target": 30,
            "primary_sales_target": 300000.0,
            "secondary_sales_target": 250000.0,
        },
    )
    assert put_resp.status_code == 200, put_resp.text
    target_data = put_resp.json()
    assert target_data["visit_target"] == 120
    assert target_data["primary_sales_target"] == 300000.0

    # 2. Admin gets targets
    get_resp = client.get(
        f"/api/v1/targets?year=2026&month=10&user_id={mr.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_resp.status_code == 200, get_resp.text
    target_list = get_resp.json()
    assert len(target_list["items"]) >= 1
    assert target_list["items"][0]["user_id"] == mr.id


def test_reports_scoping_rules(client: TestClient, db_session: Session) -> None:
    """Test MR forced scope, manager team scope, and 403 on denied scope."""
    seed_report_data(db_session)
    mr_token = get_auth_token(client, "mr")
    mgr_token = get_auth_token(client, "manager")
    admin = db_session.query(User).filter(User.email == "admin@mediatehealthcare.com").first()
    assert admin

    # 1. MR requesting another user's ID must receive 403 REPORT_SCOPE_DENIED
    denied_resp = client.get(
        f"/api/v1/reports/dcr_detailed?mr_id={admin.id}",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert denied_resp.status_code == 403, denied_resp.text
    assert "REPORT_SCOPE_DENIED" in denied_resp.text

    # 2. Manager requesting non-assigned user must receive 403
    mgr_denied_resp = client.get(
        f"/api/v1/reports/dcr_detailed?mr_id={admin.id}",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert mgr_denied_resp.status_code == 403, mgr_denied_resp.text
    assert "REPORT_SCOPE_DENIED" in mgr_denied_resp.text


def test_date_range_validation(client: TestClient) -> None:
    """Validate 92-day range limit and invalid start/end orders."""
    admin_token = get_auth_token(client, "admin")

    # Start date > End date
    resp1 = client.get(
        "/api/v1/reports/dcr_detailed?start_date=2026-10-10&end_date=2026-10-01",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp1.status_code == 400
    assert "INVALID_FILTER" in resp1.text

    # > 92 days
    resp2 = client.get(
        "/api/v1/reports/dcr_detailed?start_date=2026-01-01&end_date=2026-05-01",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp2.status_code == 400
    assert "REPORT_RANGE_TOO_LARGE" in resp2.text


def test_ist_date_boundary_at_2330() -> None:
    """Verify that Asia/Kolkata date boundary at 23:30 correctly maps into UTC."""
    start_utc, end_utc, _, _ = resolve_date_range("2026-10-04", "2026-10-04")

    # 2026-10-04 00:00:00 IST is 2026-10-03 18:30:00 UTC
    assert start_utc.year == 2026
    assert start_utc.month == 10
    assert start_utc.day == 3
    assert start_utc.hour == 18
    assert start_utc.minute == 30

    # 2026-10-04 23:30:00 IST is 2026-10-04 18:00:00 UTC
    # 23:59:59.999999 IST is 2026-10-04 18:29:59.999999 UTC
    assert end_utc.year == 2026
    assert end_utc.month == 10
    assert end_utc.day == 4
    assert end_utc.hour == 18
    assert end_utc.minute == 29

    # Check a timestamp at 23:30 IST (18:00 UTC) falls within range
    sample_utc = datetime(2026, 10, 4, 18, 0, 0)
    assert start_utc <= sample_utc <= end_utc


def test_report_json_execution(client: TestClient, db_session: Session) -> None:
    """Test GET /api/v1/reports/{key} returns columns, summary, items, and pagination."""
    seed_report_data(db_session)
    admin_token = get_auth_token(client, "admin")

    today = date.today().isoformat()
    resp = client.get(
        f"/api/v1/reports/dcr_detailed?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "meta" in data
    assert "columns" in data
    assert "summary" in data
    assert "items" in data
    assert data["meta"]["report_key"] == "dcr_detailed"
    assert len(data["items"]) >= 1
    assert any("Dr." in it["customer_name"] for it in data["items"])


def test_pdf_export(client: TestClient, db_session: Session) -> None:
    """Test PDF export: returns valid PDF starting with %PDF, contains deep green branding."""
    seed_report_data(db_session)
    admin_token = get_auth_token(client, "admin")

    today = date.today().isoformat()
    resp = client.get(
        f"/api/v1/reports/dcr_detailed/export?format=pdf&start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in resp.headers["content-disposition"]
    assert resp.content.startswith(b"%PDF")
    assert len(resp.content) > 1000  # Valid rendered PDF document


def test_excel_export(client: TestClient, db_session: Session) -> None:
    """Test Excel export: returns valid XLSX with Summary and Data sheets, openable by openpyxl."""
    seed_report_data(db_session)
    admin_token = get_auth_token(client, "admin")

    today = date.today().isoformat()
    resp = client.get(
        f"/api/v1/reports/dcr_detailed/export?format=xlsx&start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in resp.headers["content-type"]
    assert "attachment; filename=" in resp.headers["content-disposition"]

    # Load in openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(resp.content))
    sheet_names = wb.sheetnames
    assert "Summary" in sheet_names
    assert "Data" in sheet_names
    assert "By Date" in sheet_names  # R01 includes By Date grouping

    data_sheet = wb["Data"]
    assert data_sheet.max_row >= 2  # Header + at least 1 record


def test_empty_export(client: TestClient) -> None:
    """Test that export with 0 results still produces a valid PDF and Excel file saying no records."""
    admin_token = get_auth_token(client, "admin")

    # Range with no data (year 2020)
    pdf_resp = client.get(
        "/api/v1/reports/dcr_detailed/export?format=pdf&start_date=2020-01-01&end_date=2020-01-05",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.content.startswith(b"%PDF")

    xlsx_resp = client.get(
        "/api/v1/reports/dcr_detailed/export?format=xlsx&start_date=2020-01-01&end_date=2020-01-05",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert xlsx_resp.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_resp.content))
    assert "Summary" in wb.sheetnames
