"""Tests for Attendance, Pre-call Planning, DCR Visits, and Follow-ups."""

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient


def get_token(client: TestClient, role: str = "mr") -> str:
    """Helper to authenticate and get JWT access token."""
    creds = {
        "admin": ("admin@mediatehealthcare.com", "Admin@123"),
        "mr": ("mr@mediatehealthcare.com", "Mr@123"),
        "manager": ("manager@mediatehealthcare.com", "Manager@123"),
    }
    email, password = creds.get(role, ("mr@mediatehealthcare.com", "Mr@123"))
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_attendance_lifecycle(client: TestClient) -> None:
    """Verify check-in, duplicate prevention, and check-out."""
    token = get_token(client, "mr")

    # 1. Morning Check-in
    check_in_resp = client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "latitude": 19.0760,
            "longitude": 72.8777,
            "accuracy": 10.5,
            "address": "Bandra Kurla Complex, Mumbai",
            "remarks": "Started day at BKC",
            "client_uuid": "att-checkin-uuid-001",
        },
    )
    assert check_in_resp.status_code == 201, check_in_resp.text
    data = check_in_resp.json()
    assert data["status"] == "PRESENT"
    assert data["check_in_time"] is not None

    # 2. Duplicate check-in on same day should return 409
    dup_resp = client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "latitude": 19.0760,
            "longitude": 72.8777,
            "client_uuid": "att-checkin-uuid-002",
        },
    )
    assert dup_resp.status_code == 409

    # 3. Idempotent check-in with same client_uuid should return 200/201 without error
    idem_resp = client.post(
        "/api/v1/attendance/check-in",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "latitude": 19.0760,
            "longitude": 72.8777,
            "client_uuid": "att-checkin-uuid-001",
        },
    )
    assert idem_resp.status_code in [200, 201]

    # 4. Check Today status
    today_resp = client.get(
        "/api/v1/attendance/today",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert today_resp.status_code == 200
    assert today_resp.json()["id"] == data["id"]

    # 5. Evening Check-out
    check_out_resp = client.post(
        "/api/v1/attendance/check-out",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "latitude": 19.0765,
            "longitude": 72.8780,
            "remarks": "Completed daily calls",
        },
    )
    assert check_out_resp.status_code == 200, check_out_resp.text
    out_data = check_out_resp.json()
    assert out_data["check_out_time"] is not None


def test_dcr_visit_flow_with_geofence_and_followup(client: TestClient) -> None:
    """Verify DCR submission with doctor GPS, server geofence, and post-call analysis."""
    admin_token = get_token(client, "admin")
    mr_token = get_token(client, "mr")

    # 1. Create a Doctor with known coordinates
    doc_resp = client.post(
        "/api/v1/customers/doctors",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": "Dr. DCR Test Cardiologist",
            "specialization": "Cardiology",
            "category": "A",
            "phone": "9811122233",
            "latitude": 19.0520,
            "longitude": 72.8291,
        },
    )
    assert doc_resp.status_code == 201, doc_resp.text
    doctor_id = doc_resp.json()["id"]

    # 2. Create Pre-call Plan for today
    today_str = date.today().isoformat()
    plan_resp = client.post(
        "/api/v1/dcr/plans",
        headers={"Authorization": f"Bearer {mr_token}"},
        json={
            "plan_date": today_str,
            "customer_type": "DOCTOR",
            "doctor_id": doctor_id,
            "priority": "HIGH",
            "visit_purpose": "Discuss new cardiology line",
            "client_uuid": "plan-uuid-001",
        },
    )
    assert plan_resp.status_code == 201, plan_resp.text
    plan_id = plan_resp.json()["id"]

    # 3. Submit DCR Visit (Located right next to doctor: 19.05205, 72.82912)
    next_week = (date.today() + timedelta(days=7)).isoformat()
    dcr_payload = {
        "dcr_date": today_str,
        "customer_type": "DOCTOR",
        "doctor_id": doctor_id,
        "planned_visit_id": plan_id,
        "visit_type": "INDEPENDENT",
        "call_time": datetime.utcnow().isoformat(),
        "call_duration_minutes": 20,
        "latitude": 19.05205,
        "longitude": 72.82912,
        "remarks": "Doctor interested in cardio formulation",
        "pob_amount": 15000.0,
        "client_uuid": "dcr-uuid-001",
        "post_call_analysis": {
            "call_outcome": "HIGHLY_INTERESTED",
            "doctor_feedback": "Requested 5 sample strips and product brochure",
            "prescription_commitment": "HIGH",
            "next_visit_date": next_week,
            "follow_up_required": True,
            "follow_up_notes": "Deliver cardiology brochure and review sample results",
        },
        "product_details": [
            {
                "product_name": "Cardiomax 50mg",
                "sample_quantity": 5,
                "gift_quantity": 1,
                "remarks": "Table calendar gift",
            }
        ],
    }

    dcr_resp = client.post(
        "/api/v1/dcr/visits",
        headers={"Authorization": f"Bearer {mr_token}"},
        json=dcr_payload,
    )
    assert dcr_resp.status_code == 201, dcr_resp.text
    dcr_data = dcr_resp.json()

    # Verify Server Geofence
    assert dcr_data["is_geofence_verified"] is True
    assert dcr_data["distance_to_customer_meters"] is not None
    assert dcr_data["distance_to_customer_meters"] < 50.0
    assert dcr_data["pob_amount"] == 15000.0

    # Verify Post-call analysis and products
    assert dcr_data["post_call_analysis"] is not None
    assert dcr_data["post_call_analysis"]["call_outcome"] == "HIGHLY_INTERESTED"
    assert len(dcr_data["product_details"]) == 1
    assert dcr_data["product_details"][0]["product_name"] == "Cardiomax 50mg"

    # 4. Verify Linked Planned Visit was marked as COMPLETED
    plans_list = client.get(
        f"/api/v1/dcr/plans?plan_date={today_str}",
        headers={"Authorization": f"Bearer {mr_token}"},
    ).json()
    completed_plan = next((p for p in plans_list if p["id"] == plan_id), None)
    assert completed_plan is not None
    assert completed_plan["status"] == "COMPLETED"

    # 5. Verify Auto-created Follow-up (Feature 23)
    fu_resp = client.get(
        "/api/v1/dcr/follow-ups",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert fu_resp.status_code == 200
    fu_list = fu_resp.json()
    assert len(fu_list) > 0
    created_fu = fu_list[0]
    assert created_fu["doctor_id"] == doctor_id
    assert created_fu["status"] == "PENDING"

    # 6. Complete the follow-up
    comp_resp = client.post(
        f"/api/v1/dcr/follow-ups/{created_fu['id']}/complete",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "COMPLETED"

    # 7. Check Daily Summary
    summary_resp = client.get(
        f"/api/v1/dcr/summary?dcr_date={today_str}",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_calls"] >= 1
    assert summary["doctor_calls"] >= 1
    assert summary["geofence_verified_count"] >= 1
    assert summary["total_pob_amount"] >= 15000.0
