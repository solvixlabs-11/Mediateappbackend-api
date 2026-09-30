"""Tests for Users Management and Team Hierarchy (P1-B-06, P1-B-08)."""

from fastapi.testclient import TestClient


def get_token(client: TestClient, email: str, password: str) -> str:
    """Helper to authenticate and return access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    token: str = data["access_token"]
    return token


def test_admin_list_users(client: TestClient) -> None:
    """Admin can list all users across the organization."""
    admin_token = get_token(client, "admin@mediatehealthcare.com", "Admin@123")
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 3
    emails = [u["email"] for u in data["items"]]
    assert "admin@mediatehealthcare.com" in emails
    assert "manager@mediatehealthcare.com" in emails
    assert "mr@mediatehealthcare.com" in emails


def test_manager_list_users_scoped(client: TestClient) -> None:
    """Manager can only list themselves and their assigned MRs."""
    manager_token = get_token(client, "manager@mediatehealthcare.com", "Manager@123")
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    accessible_emails = {u["email"] for u in data["items"]}
    assert "manager@mediatehealthcare.com" in accessible_emails
    assert "mr@mediatehealthcare.com" in accessible_emails
    assert "admin@mediatehealthcare.com" not in accessible_emails


def test_mr_cannot_list_all_users(client: TestClient) -> None:
    """MR without users:read permission is denied 403 Forbidden."""
    mr_token = get_token(client, "mr@mediatehealthcare.com", "Mr@123")
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert response.status_code == 403


def test_manager_get_my_team(client: TestClient) -> None:
    """Manager fetches their active team members."""
    manager_token = get_token(client, "manager@mediatehealthcare.com", "Manager@123")
    response = client.get(
        "/api/v1/users/my-team",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    team = response.json()
    assert len(team) >= 1
    assert any(m["email"] == "mr@mediatehealthcare.com" for m in team)


def test_admin_create_user(client: TestClient) -> None:
    """Admin creates a new MR user with manager assignment."""
    admin_token = get_token(client, "admin@mediatehealthcare.com", "Admin@123")

    # Get manager ID
    mgr_res = client.get(
        "/api/v1/users/managers",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert mgr_res.status_code == 200
    managers = mgr_res.json()
    manager_id = managers[0]["id"]

    create_payload = {
        "email": "new.mr@mediatehealthcare.com",
        "full_name": "New MR Representative",
        "phone": "+919999988888",
        "role_code": "MR",
        "password": "Password@123",
        "manager_id": manager_id,
    }
    response = client.post(
        "/api/v1/users",
        json=create_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "new.mr@mediatehealthcare.com"
    assert user_data["role"]["code"] == "MR"
    assert user_data["current_manager"] is not None
    assert user_data["current_manager"]["id"] == manager_id


def test_deactivate_user_revokes_tokens_br14(client: TestClient) -> None:
    """BR-14: Deactivating a user immediately revokes their tokens."""
    # First login as MR to get active tokens
    mr_login = client.post(
        "/api/v1/auth/login",
        json={"email": "mr@mediatehealthcare.com", "password": "Mr@123"},
    )
    assert mr_login.status_code == 200
    mr_data = mr_login.json()
    mr_refresh_token = mr_data["refresh_token"]
    mr_id = mr_data["user"]["id"]

    # Admin deactivates MR
    admin_token = get_token(client, "admin@mediatehealthcare.com", "Admin@123")
    deactivate_res = client.patch(
        f"/api/v1/users/{mr_id}/status",
        json={"is_active": False, "reason": "Testing BR-14"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert deactivate_res.status_code == 200
    assert deactivate_res.json()["is_active"] is False

    # Attempting to refresh with the revoked token must fail with 401
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": mr_refresh_token},
    )
    assert refresh_res.status_code == 401

    # Attempting to login while deactivated must fail
    login_attempt = client.post(
        "/api/v1/auth/login",
        json={"email": "mr@mediatehealthcare.com", "password": "Mr@123"},
    )
    assert login_attempt.status_code in (401, 403)

    # Reactivate MR for subsequent tests
    reactivate_res = client.patch(
        f"/api/v1/users/{mr_id}/status",
        json={"is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["is_active"] is True


def test_profile_endpoints(client: TestClient) -> None:
    """User can view and update their own profile."""
    mr_token = get_token(client, "mr@mediatehealthcare.com", "Mr@123")

    # Get profile
    res = client.get(
        "/api/v1/users/me/profile",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert res.status_code == 200
    profile = res.json()
    assert profile["email"] == "mr@mediatehealthcare.com"
    assert profile["role"]["code"] == "MR"

    # Update profile
    update_res = client.put(
        "/api/v1/users/me/profile",
        json={"full_name": "Field MR Demo Updated", "phone": "+919111122222"},
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["full_name"] == "Field MR Demo Updated"
    assert updated["phone"] == "+919111122222"
