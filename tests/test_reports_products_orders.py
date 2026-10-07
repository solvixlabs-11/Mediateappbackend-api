"""Automated integration tests for Reports, Products Catalog, and Commercial Orders."""

from __future__ import annotations

from fastapi.testclient import TestClient


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


def test_reports_endpoint(client: TestClient) -> None:
    """Test /api/v1/reports endpoint returns valid KPIs, leaderboard, and coverage."""
    mr_token = get_auth_token(client, "mr")
    mgr_token = get_auth_token(client, "manager")
    admin_token = get_auth_token(client, "admin")

    for token in [mr_token, mgr_token, admin_token]:
        resp = client.get("/api/v1/reports/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "summary" in data
        assert "mr_performances" in data
        assert "customer_coverage" in data

        summary = data["summary"]
        assert "total_calls" in summary
        assert "doctor_calls" in summary
        assert "total_pob" in summary
        assert "average_calls_per_day" in summary


def test_products_catalog_flow(client: TestClient) -> None:
    """Test listing products, fetching categories, and product details with visual aids."""
    mr_token = get_auth_token(client, "mr")

    # 1. Create a product first (in test SQLite database)
    admin_token = get_auth_token(client, "admin")
    create_resp = client.post(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": "TEST-PRD-01",
            "name": "Diabex-Test 500",
            "brand": "Mediate Pharma",
            "category": "Diabetology",
            "composition": "Metformin 500mg",
            "packaging": "10x10 Tablets",
            "mrp": 75.0,
            "ptr": 55.0,
            "pts": 50.0,
            "indications": "Type 2 Diabetes",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    prod = create_resp.json()
    prod_id = prod["id"]

    # 2. Add visual aid slide
    aid_resp = client.post(
        f"/api/v1/products/{prod_id}/visual-aids",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Clinical Efficacy Slide",
            "slide_order": 1,
            "key_talk_points": "High efficacy, low side effects",
        },
    )
    assert aid_resp.status_code == 201, aid_resp.text

    # 3. List products
    list_resp = client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert list_resp.status_code == 200, list_resp.text
    products = list_resp.json()
    assert len(products) >= 1

    # 4. Categories list
    cat_resp = client.get(
        "/api/v1/products/categories",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert cat_resp.status_code == 200, cat_resp.text
    cats = cat_resp.json()
    assert "Diabetology" in cats

    # 5. Product detail
    detail_resp = client.get(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert len(detail["visual_aids"]) >= 1


def test_orders_booking_flow(client: TestClient) -> None:
    """Test creating and listing commercial orders."""
    mr_token = get_auth_token(client, "mr")

    # List products to get valid product_id
    prods_resp = client.get("/api/v1/products", headers={"Authorization": f"Bearer {mr_token}"})
    assert prods_resp.status_code == 200
    prods = prods_resp.json()
    assert len(prods) > 0
    p_id = prods[0]["id"]
    unit_price = prods[0]["ptr"]

    # Book order
    order_resp = client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {mr_token}"},
        json={
            "customer_type": "CHEMIST",
            "customer_id": 1,
            "payment_terms": "Net 30 Days",
            "notes": "Urgent delivery requested.",
            "items": [
                {
                    "product_id": p_id,
                    "quantity": 20,
                    "unit_price": unit_price,
                    "free_quantity": 2,
                }
            ],
        },
    )
    assert order_resp.status_code == 201, order_resp.text
    order = order_resp.json()
    assert order["status"] == "SUBMITTED"
    assert order["total_amount"] == round(20 * unit_price, 2)
    assert len(order["items"]) == 1

    # List orders
    list_resp = client.get(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert list_resp.status_code == 200, list_resp.text
    assert len(list_resp.json()) >= 1
