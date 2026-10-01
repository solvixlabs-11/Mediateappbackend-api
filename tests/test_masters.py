"""Tests for Masters and Geography module."""

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


def test_get_master_items_by_type(client: TestClient) -> None:
    """Verify master items endpoint filtered by type."""
    token = get_token(client, "admin")
    response = client.get(
        "/api/v1/masters?type=SPECIALIZATION",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0
    assert any("CARDIOLOGY" in item["code"] or "Cardiology" in item["name"] for item in items)


def test_bulk_dropdowns(client: TestClient) -> None:
    """Verify bulk dropdowns returns key-value options for all categories."""
    token = get_token(client, "mr")
    response = client.get(
        "/api/v1/masters/bulk-dropdowns",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "specializations" in data
    assert len(data["specializations"]) > 0
    spec = data["specializations"][0]
    assert "code" in spec
    assert "name" in spec
    assert "id" in spec
    assert "states" in data


def test_geography_hierarchy(client: TestClient) -> None:
    """Verify state -> city -> area hierarchy."""
    token = get_token(client, "mr")
    # 1. Get States
    states_resp = client.get(
        "/api/v1/masters/states",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert states_resp.status_code == 200
    states = states_resp.json()
    assert len(states) > 0
    mh = next((s for s in states if s["code"] == "MH"), states[0])

    # 2. Get Cities for State
    cities_resp = client.get(
        f"/api/v1/masters/cities?state_id={mh['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cities_resp.status_code == 200
    cities = cities_resp.json()
    assert len(cities) > 0

    # 3. Get Areas for City
    city_id = cities[0]["id"]
    areas_resp = client.get(
        f"/api/v1/masters/areas?city_id={city_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert areas_resp.status_code == 200
    areas = areas_resp.json()
    assert isinstance(areas, list)


def test_create_master_item_admin(client: TestClient) -> None:
    """Verify admin can create a custom master item."""
    token = get_token(client, "admin")
    response = client.post(
        "/api/v1/masters",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "SPECIALIZATION",
            "code": "RHEUMATOLOGY_CUSTOM",
            "name": "Rheumatology Custom",
            "display_order": 99,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "RHEUMATOLOGY_CUSTOM"
    assert data["name"] == "Rheumatology Custom"


def test_create_master_item_mr_forbidden(client: TestClient) -> None:
    """Verify MR role cannot create a master item."""
    token = get_token(client, "mr")
    response = client.post(
        "/api/v1/masters",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "SPECIALIZATION",
            "code": "TEST_SPEC",
            "name": "Test Spec",
        },
    )
    assert response.status_code == 403
