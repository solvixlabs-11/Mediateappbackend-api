"""Tests for StorageProvider and Files endpoints (P1-B-07)."""

import io

from fastapi.testclient import TestClient


def get_token(client: TestClient, email: str, password: str) -> str:
    """Helper to authenticate and return access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token: str = response.json()["access_token"]
    return token


def test_file_upload_and_download(client: TestClient) -> None:
    """Upload an image file and download it back."""
    token = get_token(client, "admin@mediatehealthcare.com", "Admin@123")

    fake_image_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtest-image-content"
    file_tuple = ("test_avatar.png", io.BytesIO(fake_image_content), "image/png")

    # 1. Upload
    upload_res = client.post(
        "/api/v1/files/upload",
        files={"file": file_tuple},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_res.status_code == 201
    file_data = upload_res.json()
    assert "id" in file_data
    assert file_data["original_filename"] == "test_avatar.png"
    assert file_data["mime_type"] == "image/png"
    file_id = file_data["id"]

    # 2. Get file metadata
    meta_res = client.get(
        f"/api/v1/files/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert meta_res.status_code == 200
    assert meta_res.json()["id"] == file_id

    # 3. Download binary content
    download_res = client.get(f"/api/v1/files/{file_id}/download")
    assert download_res.status_code == 200
    assert download_res.content == fake_image_content
    assert download_res.headers["content-type"] == "image/png"


def test_file_upload_invalid_type(client: TestClient) -> None:
    """Reject unsupported file types with 400 Bad Request."""
    token = get_token(client, "admin@mediatehealthcare.com", "Admin@123")

    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
    file_tuple = ("malware.exe", io.BytesIO(fake_exe), "application/x-dosexec")

    response = client.post(
        "/api/v1/files/upload",
        files={"file": file_tuple},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_user_avatar_link_to_profile(client: TestClient) -> None:
    """Upload avatar and associate it with user profile."""
    token = get_token(client, "mr@mediatehealthcare.com", "Mr@123")

    fake_avatar = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!"
        b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
        b"\x00\x02\x02D\x01\x00;"
    )
    file_tuple = ("avatar.gif", io.BytesIO(fake_avatar), "image/gif")

    upload_res = client.post(
        "/api/v1/files/upload",
        files={"file": file_tuple},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["id"]

    # Link to profile
    update_res = client.put(
        "/api/v1/users/me/profile",
        json={"profile_picture_file_id": file_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 200
    profile = update_res.json()
    assert profile["profile_picture_file_id"] == file_id
    assert profile["profile_picture_url"] is not None
    assert f"/files/{file_id}/download" in profile["profile_picture_url"]
