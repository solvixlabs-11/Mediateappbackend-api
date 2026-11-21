
"""Tests for Sales Targets API (CRUD and Scoping)."""

from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.attendance.models import Attendance
from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrProductDetail, DcrVisit, PlannedVisit
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
    """Helper to seed sample records for targets testing."""
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
        db.commit()
        db.refresh(terr)

    mr_terr = (
        db.query(UserTerritoryAssignment)
        .filter(
            UserTerritoryAssignment.user_id == mr.id,
            UserTerritoryAssignment.territory_id == terr.id,
        )
        .first()
    )
    if not mr_terr:
        db.add(UserTerritoryAssignment(user_id=mr.id, territory_id=terr.id))
        db.commit()

    # Create manager assignment
    mgr_assign = (
        db.query(ManagerMRAssignment)
        .filter(
            ManagerMRAssignment.manager_id == manager.id,
            ManagerMRAssignment.mr_id == mr.id,
        )
        .first()
    )
    if not mgr_assign:
        db.add(ManagerMRAssignment(manager_id=manager.id, mr_id=mr.id))
        db.commit()

    return {
        "admin_id": admin.id,
        "manager_id": manager.id,
        "mr_id": mr.id,
        "territory_id": terr.id,
    }


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
