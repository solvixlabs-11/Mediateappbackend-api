"""Tests for Dynamic Navigation Menu endpoint."""

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


def test_navigation_menu_unauthorized(client: TestClient) -> None:
    """Unauthenticated request must return 401."""
    response = client.get("/api/v1/navigation/menu")
    assert response.status_code == 401


def test_navigation_menu_admin(client: TestClient) -> None:
    """Admin user fetches all 103 dynamic inventory menu items across 6 groups."""
    token = get_token(client, "admin")
    response = client.get(
        "/api/v1/navigation/menu",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["totalItems"] == 103
    assert data["permittedItems"] == 103
    assert len(data["groups"]) == 6

    group_keys = [g["key"] for g in data["groups"]]
    assert group_keys == [
        "masters",
        "parameters",
        "reports",
        "activities",
        "utility",
        "detail-reports",
    ]

    # Verify all items have valid routes and tiers
    valid_statuses = {"HAVE", "PARTIAL", "NEW", "UNKNOWN"}
    valid_tiers = {"T1", "T2", "T3", "T4", "T5"}
    for item in data["allItems"]:
        assert item["path"].startswith("/")
        assert item["status"] in valid_statuses
        assert item["tier"] in valid_tiers
        assert item["purpose"]
        assert item["label"]


def test_quick_cards_endpoint(client: TestClient) -> None:
    """Verify dynamic quick cards for admin and manager."""
    admin_token = get_token(client, "admin")
    admin_res = client.get(
        "/api/v1/navigation/quick-cards",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200
    cards = admin_res.json()
    assert len(cards) >= 6
    card_ids = [c["id"] for c in cards]
    assert "users" in card_ids
    assert "customers" in card_ids
    assert "masters" in card_ids
    assert "territories" in card_ids


def test_mobile_drawer_endpoint(client: TestClient) -> None:
    """Verify dynamic mobile drawer navigation items."""
    mr_token = get_token(client, "mr")
    res = client.get(
        "/api/v1/navigation/mobile-drawer",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 10
    assert any(i["key"] == "my_visits" for i in items)

