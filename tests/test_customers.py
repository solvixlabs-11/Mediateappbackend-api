"""Tests for Territories and Customers (Doctors, Hospitals, Chemists, Stockists) module."""

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


def test_territory_crud_and_assignment(client: TestClient) -> None:
    """Verify territory creation and user assignment."""
    admin_token = get_token(client, "admin")
    mr_token = get_token(client, "mr")

    # 1. Create territory
    create_resp = client.post(
        "/api/v1/territories",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "South Mumbai Cardio",
            "code": "SO_MUM_01",
            "headquarters": "Mumbai",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    territory_id = create_resp.json()["id"]

    # 2. Get MR user ID
    mr_profile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {mr_token}"},
    ).json()
    mr_id = mr_profile["id"]

    # 3. Assign MR to territory
    assign_resp = client.post(
        f"/api/v1/territories/{territory_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"user_id": mr_id},
    )
    assert assign_resp.status_code == 200, assign_resp.text

    # 4. Check MR sees their assigned territory
    mr_territories = client.get(
        "/api/v1/territories/my-territories",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert mr_territories.status_code == 200
    assigned_list = mr_territories.json()
    assert any(t["id"] == territory_id for t in assigned_list)


def test_customer_lifecycle_and_nearby(client: TestClient) -> None:
    """Verify Hospital, Doctor, Chemist lifecycle and Haversine nearby query."""
    admin_token = get_token(client, "admin")
    mr_token = get_token(client, "mr")

    # 1. Create Territory
    t_resp = client.post(
        "/api/v1/territories",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Bandra West",
            "code": "BANDRA_W",
            "headquarters": "Mumbai",
        },
    )
    assert t_resp.status_code == 201, t_resp.text
    territory_id = t_resp.json()["id"]

    # Assign MR
    mr_profile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {mr_token}"},
    ).json()
    client.post(
        f"/api/v1/territories/{territory_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"user_id": mr_profile["id"]},
    )

    # 2. Create Hospital
    hosp_resp = client.post(
        "/api/v1/customers/hospitals",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Lilavati Hospital",
            "territory_id": territory_id,
            "address": "Bandra Reclamation, Bandra West",
            "latitude": 19.0519,
            "longitude": 72.8290,
            "bed_count": 300,
        },
    )
    assert hosp_resp.status_code == 201, hosp_resp.text
    hospital_id = hosp_resp.json()["id"]

    # 3. Create Doctor
    doc_resp = client.post(
        "/api/v1/customers/doctors",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": "Dr. Rajesh Sharma",
            "qualification": "MBBS, MD (Cardiology)",
            "specialization": "Cardiology",
            "category": "A",
            "phone": "9876543210",
            "email": "dr.rajesh@lilavati.org",
            "territory_id": territory_id,
            "clinic_name": "Lilavati Hospital OPD 4",
            "address": "Bandra Reclamation",
            "latitude": 19.0520,
            "longitude": 72.8291,
        },
    )
    assert doc_resp.status_code == 201, doc_resp.text
    doctor_id = doc_resp.json()["id"]

    # Map Doctor to Hospital
    map_resp = client.post(
        "/api/v1/customers/hospitals/map-doctor",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "hospital_id": hospital_id,
            "doctor_id": doctor_id,
            "department": "Cardiology",
            "is_primary": True,
        },
    )
    assert map_resp.status_code == 200

    # 4. Create Chemist
    chem_resp = client.post(
        "/api/v1/customers/chemists",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "shop_name": "Apollo Pharmacy Bandra",
            "contact_person": "Sunil Gupta",
            "phone": "9876500001",
            "territory_id": territory_id,
            "address": "Near Lilavati Hospital, Bandra",
            "latitude": 19.0522,
            "longitude": 72.8292,
        },
    )
    assert chem_resp.status_code == 201, chem_resp.text

    # 5. Test Nearby query (located right next to Lilavati: 19.05195, 72.82905)
    nearby_resp = client.get(
        "/api/v1/customers/nearby?latitude=19.05195&longitude=72.82905&radius_meters=500",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert nearby_resp.status_code == 200
    nearby_items = nearby_resp.json()

    # Doctor should be found and in geofence
    found_doc = next(
        (d for d in nearby_items if d["id"] == doctor_id and d["customer_type"] == "DOCTOR"),
        None,
    )
    assert found_doc is not None
    assert found_doc["in_geofence"] is True
    assert found_doc["distance_meters"] < 100.0

    # 6. Test Doctor Detail
    detail_resp = client.get(
        f"/api/v1/customers/doctors/{doctor_id}",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert detail_resp.status_code == 200
    doc_detail = detail_resp.json()
    assert doc_detail["full_name"] == "Dr. Rajesh Sharma"
    assert len(doc_detail["hospitals"]) == 1
    assert doc_detail["hospitals"][0]["hospital_id"] == hospital_id


def test_customer_csv_import(client: TestClient) -> None:
    """Verify CSV import endpoint for bulk seeding doctors."""
    admin_token = get_token(client, "admin")

    # Create territory first
    t_resp = client.post(
        "/api/v1/territories",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Imports Territory", "code": "IMP_01", "headquarters": "Delhi"},
    )
    assert t_resp.status_code == 201

    csv_lines = [
        "full_name,specialization,category,phone,clinic_name,address,latitude,longitude",
        "Dr. Imported One,Pediatrics,A,9123456780,Child Clinic,Main Road,28.6139,77.2090",
        "Dr. Imported Two,Orthopedics,B,9123456781,Bone Clinic,Second Cross,28.6140,77.2092",
    ]
    csv_content = "\n".join(csv_lines) + "\n"

    files = {"file": ("doctors.csv", csv_content.encode("utf-8"), "text/csv")}
    import_resp = client.post(
        "/api/v1/customers/import?entity_type=DOCTOR",
        headers={"Authorization": f"Bearer {admin_token}"},
        files=files,
    )
    assert import_resp.status_code == 200, import_resp.text
    result = import_resp.json()
    assert result["imported_count"] == 2
    assert result["failed_count"] == 0
