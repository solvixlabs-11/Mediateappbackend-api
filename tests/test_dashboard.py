"""Tests for Dashboard module including Admin Live Field Activity and role metrics."""

from fastapi.testclient import TestClient


def get_token(client: TestClient, role: str = "admin") -> str:
    """Helper to authenticate and get JWT access token."""
    creds = {
        "admin": ("admin@mediatehealthcare.com", "Admin@123"),
        "mr": ("mr@mediatehealthcare.com", "Mr@123"),
        "manager": ("manager@mediatehealthcare.com", "Manager@123"),
    }
    email, password = creds.get(role, ("admin@mediatehealthcare.com", "Admin@123"))
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_admin_live_activity_endpoint(client: TestClient) -> None:
    """Verify Section 8.2 Admin Home Live Field Activity response structure."""
    admin_token = get_token(client, "admin")
    manager_token = get_token(client, "manager")
    mr_token = get_token(client, "mr")

    # 1. Admin access
    resp = client.get(
        "/api/v1/dashboard/admin/live-activity",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Verify Summary strip
    assert "summary" in data
    summary = data["summary"]
    assert "checked_in_count" in summary
    assert "total_mrs" in summary
    assert "total_calls_today" in summary
    assert "doctors_visited" in summary
    assert "chemists_visited" in summary
    assert "total_pob_today" in summary
    assert "attendance_pct" in summary
    assert "not_checked_in_count" in summary

    # Verify MR activity cards
    assert "mr_activities" in data
    assert isinstance(data["mr_activities"], list)
    if data["mr_activities"]:
        mr_card = data["mr_activities"][0]
        assert "user_id" in mr_card
        assert "mr_name" in mr_card
        assert "employee_code" in mr_card
        assert "status" in mr_card
        assert mr_card["status"] in ("VISITING", "CHECKED_IN", "IDLE", "NOT_CHECKED_IN", "ON_LEAVE")
        assert "calls_count" in mr_card
        assert "doctors_count" in mr_card
        assert "chemists_count" in mr_card
        assert "calls_target" in mr_card
        assert "is_verified" in mr_card

    # Verify Pending approvals summary
    assert "pending_approvals" in data
    pending = data["pending_approvals"]
    assert "tours_count" in pending
    assert "expenses_count" in pending
    assert "leaves_count" in pending
    assert "total_pending" in pending

    # 2. Manager access is also allowed
    mgr_resp = client.get(
        "/api/v1/dashboard/admin/live-activity",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert mgr_resp.status_code == 200

    # 3. MR role is forbidden
    mr_resp = client.get(
        "/api/v1/dashboard/admin/live-activity",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert mr_resp.status_code == 403


def test_mr_dashboard_endpoint(client: TestClient) -> None:
    """Verify MR's personal performance endpoint."""
    mr_token = get_token(client, "mr")

    resp = client.get(
        "/api/v1/dashboard/mr",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "user_id" in data
    assert "today_date" in data
    assert "attendance_status" in data
    assert data["attendance_status"] in ("CHECKED_IN", "CHECKED_OUT", "NOT_CHECKED_IN")
    assert "visits_today" in data
    assert "visits_target" in data
    assert "pob_today" in data
    assert "monthly_visits" in data
    assert "monthly_target" in data
    assert "monthly_pob" in data
    assert "pending_followups_count" in data


def test_manager_dashboard_endpoint(client: TestClient) -> None:
    """Verify Manager's team oversight dashboard endpoint."""
    manager_token = get_token(client, "manager")
    mr_token = get_token(client, "mr")

    resp = client.get(
        "/api/v1/dashboard/manager",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "team_size" in data
    assert "checked_in_today" in data
    assert "calls_today" in data
    assert "total_pob_today" in data
    assert "pending_approvals_count" in data
    assert "team_coverage_pct" in data

    # MR role should not be allowed to access manager dashboard
    mr_resp = client.get(
        "/api/v1/dashboard/manager",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert mr_resp.status_code == 403
