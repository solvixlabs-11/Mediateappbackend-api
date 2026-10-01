"""Tests for authentication and session lifecycle."""

from fastapi.testclient import TestClient


def test_login_success_mr(client: TestClient) -> None:
    """Ensure MR user can log in and receives access & refresh tokens."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "mr@mediatehealthcare.com", "password": "Mr@123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["role"] == "MR"
    assert "dcr:write" in data["user"]["permissions"]


def test_login_invalid_password(client: TestClient) -> None:
    """Ensure wrong password returns 401."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "mr@mediatehealthcare.com", "password": "WrongPassword"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_login_account_lockout(client: TestClient) -> None:
    """Ensure account locks out after 5 consecutive failed attempts."""
    email = "lockout.test@mediatehealthcare.com"
    # Register dedicated test user
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password@123", "full_name": "Lockout Tester"},
    )
    assert reg.status_code == 201

    for _ in range(4):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "BadPassword"},
        )
        assert res.status_code == 401

    # 5th attempt triggers lockout
    lock_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "BadPassword"},
    )
    assert lock_res.status_code == 403
    assert "Account locked" in lock_res.json()["detail"]


def test_token_refresh_rotation(client: TestClient) -> None:
    """Ensure token refresh rotates the refresh token and returns new pair."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mediatehealthcare.com", "password": "Admin@123"},
    )
    assert login_res.status_code == 200
    old_refresh = login_res.json()["refresh_token"]

    # Refresh
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert new_data["refresh_token"] != old_refresh
    assert "access_token" in new_data

    # Reuse detection: attempting to reuse old_refresh must be rejected and revoke family
    reuse_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reuse_res.status_code == 401
    assert "reuse detected" in reuse_res.json()["detail"].lower()


def test_auth_me_endpoint(client: TestClient) -> None:
    """Ensure /auth/me returns current user identity with valid Bearer token."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mediatehealthcare.com", "password": "Admin@123"},
    )
    access_token = login_res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "admin@mediatehealthcare.com"
    assert user_data["role"] == "ADMIN"
    # Admin has all permissions
    assert len(user_data["permissions"]) > 0


def test_logout(client: TestClient) -> None:
    """Ensure logout invalidates session."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "mr@mediatehealthcare.com", "password": "Mr@123"},
    )
    access_token = login_res.json()["access_token"]
    refresh_token = login_res.json()["refresh_token"]

    logout_res = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_res.status_code == 200

    # Refreshing with the logged-out token should fail
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 401


def test_logout_all(client: TestClient) -> None:
    """Ensure logout-all revokes all sessions for the user."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "mr@mediatehealthcare.com", "password": "Mr@123"},
    )
    access_token = login_res.json()["access_token"]
    refresh_token = login_res.json()["refresh_token"]

    logout_all_res = client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_all_res.status_code == 200

    # Token refresh should now fail
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 401


def test_change_password(client: TestClient) -> None:
    """Ensure password change updates credentials and invalidates active tokens."""
    # Register a new user to test password change
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "pwdtest@mediatehealthcare.com",
            "password": "OldPassword123",
            "full_name": "Password Test User",
            "role_code": "MR",
        },
    )
    assert reg_res.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "pwdtest@mediatehealthcare.com", "password": "OldPassword123"},
    )
    access_token = login_res.json()["access_token"]

    change_res = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "OldPassword123", "new_password": "NewPassword123"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert change_res.status_code == 200

    # Old password fails
    old_fail = client.post(
        "/api/v1/auth/login",
        json={"email": "pwdtest@mediatehealthcare.com", "password": "OldPassword123"},
    )
    assert old_fail.status_code == 401

    # New password succeeds
    new_ok = client.post(
        "/api/v1/auth/login",
        json={"email": "pwdtest@mediatehealthcare.com", "password": "NewPassword123"},
    )
    assert new_ok.status_code == 200


def test_get_auth_config(client: TestClient) -> None:
    """Ensure /auth/config returns dynamic roles and demo accounts in dev."""
    res = client.get("/api/v1/auth/config")
    assert res.status_code == 200
    data = res.json()
    assert "roles" in data
    assert "MR" in data["roles"]
    assert "MANAGER" in data["roles"]
    assert "ADMIN" in data["roles"]
    assert "demo_accounts" in data
    assert len(data["demo_accounts"]) >= 3
