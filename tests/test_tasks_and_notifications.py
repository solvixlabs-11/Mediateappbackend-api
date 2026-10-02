"""Automated integration tests for Tasks, Comments, and Notifications."""

from __future__ import annotations

import datetime as dt

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


def test_tasks_crud_and_comments(client: TestClient) -> None:
    """Test full operational lifecycle of a Task with discussion comments."""
    mr_token = get_auth_token(client, "mr")
    mgr_token = get_auth_token(client, "manager")

    # Get MR info
    mr_me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {mr_token}"})
    assert mr_me_resp.status_code == 200, mr_me_resp.text
    mr_user_id = mr_me_resp.json()["id"]

    # 1. Summary counters
    sum_resp = client.get(
        "/api/v1/tasks/summary",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert sum_resp.status_code == 200, sum_resp.text
    summary = sum_resp.json()
    assert "today_count" in summary
    assert "upcoming_count" in summary
    assert "overdue_count" in summary
    assert "completed_count" in summary

    # 2. List MR tasks
    list_resp = client.get(
        "/api/v1/tasks",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert list_resp.status_code == 200, list_resp.text
    tasks = list_resp.json()
    assert isinstance(tasks, list)

    # 3. Create a new task by Manager assigned to MR
    due_date = dt.date.today() + dt.timedelta(days=3)
    create_resp = client.post(
        "/api/v1/tasks",
        headers={"Authorization": f"Bearer {mgr_token}"},
        json={
            "title": "Collect Clinical Feedback on Diabex 500",
            "description": "Urgent feedback required for regional review meeting.",
            "due_date": due_date.isoformat(),
            "priority": "HIGH",
            "assigned_to_id": mr_user_id,
            "customer_type": "DOCTOR",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    task_id = created["id"]
    assert created["title"] == "Collect Clinical Feedback on Diabex 500"
    assert created["status"] == "PENDING"
    assert created["priority"] == "HIGH"
    assert created["assigned_to_id"] == mr_user_id

    # 4. MR adds comment to task
    comment_resp = client.post(
        f"/api/v1/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {mr_token}"},
        json={"message": "Acknowledged. Visiting the clinic tomorrow morning."},
    )
    assert comment_resp.status_code == 201, comment_resp.text
    c_data = comment_resp.json()
    assert c_data["message"] == "Acknowledged. Visiting the clinic tomorrow morning."

    # 5. Fetch detail - verify comments list
    detail_resp = client.get(
        f"/api/v1/tasks/{task_id}",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["comments_count"] >= 1
    assert any("Acknowledged" in c["message"] for c in detail["comments"])

    # 6. Toggle completion
    comp_resp = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert comp_resp.status_code == 200, comp_resp.text
    assert comp_resp.json()["status"] == "COMPLETED"
    assert comp_resp.json()["completed_at"] is not None


def test_notifications_flow(client: TestClient) -> None:
    """Test notification listing, summary, reading, and device token registration."""
    mr_token = get_auth_token(client, "mr")
    admin_token = get_auth_token(client, "admin")

    mr_me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {mr_token}"})
    assert mr_me_resp.status_code == 200, mr_me_resp.text
    mr_user_id = mr_me_resp.json()["id"]

    # 1. Trigger / Create a notification for MR
    notif_create_resp = client.post(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "user_id": mr_user_id,
            "title": "Tour Program Approved",
            "body": "Your tour program for Pune region has been approved.",
            "notification_type": "TOUR",
            "reference_id": "101",
        },
    )
    assert notif_create_resp.status_code == 201, notif_create_resp.text
    created_notif = notif_create_resp.json()
    target_id = created_notif["id"]

    # 2. Summary
    sum_resp = client.get(
        "/api/v1/notifications/summary",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert sum_resp.status_code == 200, sum_resp.text
    summary = sum_resp.json()
    assert summary["unread_count"] >= 1
    assert summary["total_count"] >= 1

    # 3. List notifications
    list_resp = client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert list_resp.status_code == 200, list_resp.text
    notifs = list_resp.json()
    assert isinstance(notifs, list)
    assert len(notifs) >= 1

    # 4. Mark single as read
    read_resp = client.post(
        f"/api/v1/notifications/{target_id}/read",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert read_resp.status_code == 200, read_resp.text
    assert read_resp.json()["is_read"] is True

    # 5. Mark all as read
    mark_all = client.post(
        "/api/v1/notifications/read-all",
        headers={"Authorization": f"Bearer {mr_token}"},
    )
    assert mark_all.status_code == 200, mark_all.text
    assert "marked_read_count" in mark_all.json()

    # 6. Register device token
    token_resp = client.post(
        "/api/v1/notifications/device-token",
        headers={"Authorization": f"Bearer {mr_token}"},
        json={
            "token": "fcm_mock_device_token_xyz_1234567890",
            "platform": "ANDROID",
        },
    )
    assert token_resp.status_code == 200, token_resp.text
    assert token_resp.json()["platform"] == "ANDROID"
    assert token_resp.json()["is_active"] is True
