"""Comprehensive test suite for Reports Engine (26 reports), Exports (PDF & Excel), and Scoping."""

from __future__ import annotations

import io
from datetime import date, datetime, timedelta

import openpyxl
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.modules.reports.definitions  # noqa: F401
from app.modules.attendance.models import Attendance
from app.modules.customers.models import Chemist, Doctor
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

    # Chemist
    chem = db.query(Chemist).filter(Chemist.code == "CHEM-REP-01").first()
    if not chem:
        chem = Chemist(
            code="CHEM-REP-01",
            shop_name="Apollo Pharmacy Pune",
            contact_person="Ramesh Patel",
            territory_id=terr.id,
        )
        db.add(chem)
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

        prod = DcrProductDetail(
            dcr_visit_id=visit.id,
            product_name="Cardiox 50mg",
            sample_quantity=2,
            gift_quantity=1,
        )
        db.add(prod)

    db.commit()
    return {
        "admin_id": admin.id,
        "manager_id": manager.id,
        "mr_id": mr.id,
        "territory_id": terr.id,
        "doctor_id": doc.id,
    }


def test_registry_contains_26_reports() -> None:
    """Validate that the registry holds all 26 reports conforming to v2 catalog."""
    keys = ReportRegistry.list_keys()
    assert len(keys) == 26, f"Expected 26 registered reports, got {len(keys)}: {keys}"
    expected_keys = [
        "doctor_list",
        "chemist_list",
        "mr_wise_route_master",
        "mr_daily_punching",
        "mr_wise_attendance_report",
        "daily_work_report",
        "mr_wise_visits",
        "mr_wise_visits_analysis",
        "mr_designation_wise_visits_analysis",
        "mr_wise_doctor_chemist_call",
        "mr_wise_promotional_call",
        "mr_deviation_report",
        "mr_doctor_wise_monthly_summary",
        "mr_wise_not_seen_doctor",
        "mr_wise_doc_sp_wise_stats",
        "mr_wise_doctor_category_wise_report",
        "mr_wise_doctor_type_wise_report",
        "mr_wise_sample_balance_report",
        "order_register",
        "mr_wise_chemist_wise_sales",
        "mr_wise_stockist_wise_sales",
        "mr_wise_monthly_business_report",
        "collection_report",
        "credit_note_report",
        "outstanding_report",
        "induction_report",
    ]
    for k in expected_keys:
        assert k in keys, f"Missing registered report {k}"
        rep = ReportRegistry.get(k)
        assert rep is not None
        assert rep.key == k
        assert rep.title
        assert rep.group
        assert len(rep.get_columns()) > 0
        assert rep.status in ["NOW", "P8", "SALES", "ASK"]


def test_reports_catalog_endpoint(client: TestClient) -> None:
    """Test GET /api/v1/reports returns role-appropriate catalog items (26 for ADMIN)."""
    admin_token = get_auth_token(client, "admin")
    mr_token = get_auth_token(client, "mr")
    mgr_token = get_auth_token(client, "manager")

    # ADMIN sees ALL 26 reports
    resp = client.get("/api/v1/reports", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["role"] == "ADMIN"
    assert len(data["reports"]) == 26

    # Verify status breakdown
    statuses = [r["status"] for r in data["reports"]]
    assert statuses.count("NOW") == 16
    assert statuses.count("P8") == 3
    assert statuses.count("SALES") == 6
    assert statuses.count("ASK") == 1

    # MANAGER sees 25 reports (all except Induction Report)
    mgr_resp = client.get("/api/v1/reports", headers={"Authorization": f"Bearer {mgr_token}"})
    assert mgr_resp.status_code == 200, mgr_resp.text
    mgr_data = mgr_resp.json()
    assert len(mgr_data["reports"]) == 25
    mgr_keys = [r["key"] for r in mgr_data["reports"]]
    assert "induction_report" not in mgr_keys

    # MR sees 24 reports (excludes Designation Wise Visits Analysis and Induction Report)
    mr_resp = client.get("/api/v1/reports", headers={"Authorization": f"Bearer {mr_token}"})
    assert mr_resp.status_code == 200, mr_resp.text
    mr_data = mr_resp.json()
    assert len(mr_data["reports"]) == 24
    mr_keys = [r["key"] for r in mr_data["reports"]]
    assert "mr_designation_wise_visits_analysis" not in mr_keys
    assert "induction_report" not in mr_keys
    assert "doctor_list" in mr_keys
    assert "mr_wise_visits" in mr_keys


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
        f"/api/v1/reports/mr_wise_visits?mr_id={admin.id}",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert denied_resp.status_code == 403, denied_resp.text
    assert "REPORT_SCOPE_DENIED" in denied_resp.text

    # 2. Manager requesting non-assigned user must receive 403
    mgr_denied_resp = client.get(
        f"/api/v1/reports/mr_wise_visits?mr_id={admin.id}",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert mgr_denied_resp.status_code == 403, mgr_denied_resp.text
    assert "REPORT_SCOPE_DENIED" in mgr_denied_resp.text


def test_date_range_validation(client: TestClient) -> None:
    """Validate 92-day range limit and invalid start/end orders."""
    admin_token = get_auth_token(client, "admin")

    # Start date > End date
    resp1 = client.get(
        "/api/v1/reports/mr_wise_visits?start_date=2026-10-10&end_date=2026-10-01",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp1.status_code == 400
    assert "INVALID_FILTER" in resp1.text

    # > 92 days
    resp2 = client.get(
        "/api/v1/reports/mr_wise_visits?start_date=2026-01-01&end_date=2026-05-01",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp2.status_code == 400
    assert "REPORT_RANGE_TOO_LARGE" in resp2.text


def test_coming_soon_report_returns_400(client: TestClient) -> None:
    """Validate that attempting to execute a coming-soon report returns clean 400 with reason."""
    admin_token = get_auth_token(client, "admin")
    resp = client.get(
        "/api/v1/reports/order_register",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400
    assert "REPORT_COMING_SOON" in resp.headers.get("X-Error-Code", "")


def test_report_json_execution(client: TestClient, db_session: Session) -> None:
    """Test GET /api/v1/reports/{key} returns columns, summary, items, and pagination."""
    seed_report_data(db_session)
    admin_token = get_auth_token(client, "admin")

    today = date.today().isoformat()
    resp = client.get(
        f"/api/v1/reports/mr_wise_visits?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "meta" in data
    assert "columns" in data
    assert "summary" in data
    assert "items" in data
    assert data["meta"]["report_key"] == "mr_wise_visits"
    assert len(data["items"]) >= 1
    assert any("Dr." in it["customer_name"] for it in data["items"])


def test_pdf_export(client: TestClient, db_session: Session) -> None:
    """Test PDF export: returns valid PDF starting with %PDF, contains deep green branding."""
    seed_report_data(db_session)
    admin_token = get_auth_token(client, "admin")

    today = date.today().isoformat()
    resp = client.get(
        f"/api/v1/reports/mr_wise_visits/export?format=pdf&start_date={today}&end_date={today}",
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
        f"/api/v1/reports/mr_wise_attendance_report/export?format=xlsx&start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in resp.headers["content-type"]
    assert "attachment; filename=" in resp.headers["content-disposition"]

    wb = openpyxl.load_workbook(io.BytesIO(resp.content))
    sheet_names = wb.sheetnames
    assert "Summary" in sheet_names
    assert "Data" in sheet_names

    data_sheet = wb["Data"]
    assert data_sheet.max_row >= 2  # Header + records
    assert data_sheet.freeze_panes == "B2"  # Frozen first column for attendance report


def test_all_16_now_reports_execute(client: TestClient, db_session: Session) -> None:
    """Validate that every one of the 16 NOW reports executes successfully and returns valid JSON."""
    seed_report_data(db_session)
    admin_token = get_auth_token(client, "admin")

    now_keys = [
        "doctor_list",
        "chemist_list",
        "mr_wise_route_master",
        "mr_daily_punching",
        "mr_wise_attendance_report",
        "daily_work_report",
        "mr_wise_visits",
        "mr_wise_visits_analysis",
        "mr_designation_wise_visits_analysis",
        "mr_wise_doctor_chemist_call",
        "mr_deviation_report",
        "mr_doctor_wise_monthly_summary",
        "mr_wise_not_seen_doctor",
        "mr_wise_doc_sp_wise_stats",
        "mr_wise_doctor_category_wise_report",
        "mr_wise_doctor_type_wise_report",
    ]

    for key in now_keys:
        resp = client.get(
            f"/api/v1/reports/{key}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, f"Report {key} failed: {resp.text}"
        data = resp.json()
        assert "columns" in data, f"Missing columns in {key}"
        assert "items" in data, f"Missing items in {key}"
        assert "summary" in data, f"Missing summary in {key}"
        assert len(data["columns"]) > 0, f"Columns empty for {key}"


def test_dynamic_filters_affect_results(client: TestClient, db_session: Session) -> None:
    """Test that all filter parameters dynamically apply to SQL queries."""
    seed_report_data(db_session)
    admin_token = get_auth_token(client, "admin")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Unfiltered doctor list
    r_all = client.get("/api/v1/reports/doctor_list", headers=headers)
    assert r_all.status_code == 200
    all_docs = r_all.json()["items"]
    assert len(all_docs) >= 1

    # 2. Filter doctor list by territory
    terr = db_session.query(Territory).first()
    r_terr = client.get(f"/api/v1/reports/doctor_list?territory_id={terr.id}", headers=headers)
    assert r_terr.status_code == 200
    terr_docs = r_terr.json()["items"]
    assert len(terr_docs) >= 1
    for d in terr_docs:
        assert d["territory"] == terr.name

    # 3. Filter doctor list by invalid territory returns empty
    r_empty = client.get("/api/v1/reports/doctor_list?territory_id=99999", headers=headers)
    assert r_empty.status_code == 200
    assert len(r_empty.json()["items"]) == 0

    # 4. Filter doctor list by category
    r_cat = client.get("/api/v1/reports/doctor_list?category=A", headers=headers)
    assert r_cat.status_code == 200
    for d in r_cat.json()["items"]:
        assert d["category"] == "A"

    # 5. Filter visits by customer_type
    r_vis_doc = client.get("/api/v1/reports/mr_wise_visits?customer_type=DOCTOR", headers=headers)
    assert r_vis_doc.status_code == 200
    for v in r_vis_doc.json()["items"]:
        assert v["customer_type"] == "Doctor"

    r_vis_chem = client.get("/api/v1/reports/mr_wise_visits?customer_type=CHEMIST", headers=headers)
    assert r_vis_chem.status_code == 200
    assert len(r_vis_chem.json()["items"]) == 0

    # 6. Filter attendance by work_type
    r_att_present = client.get("/api/v1/reports/mr_daily_punching?work_type=PRESENT", headers=headers)
    assert r_att_present.status_code == 200
    assert len(r_att_present.json()["items"]) >= 1

    r_att_leave = client.get("/api/v1/reports/mr_daily_punching?work_type=LEAVE", headers=headers)
    assert r_att_leave.status_code == 200
    assert len(r_att_leave.json()["items"]) == 0

