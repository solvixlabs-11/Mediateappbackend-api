"""Tests for health and readiness endpoints."""

from fastapi.testclient import TestClient


def test_health_check_returns_200(client: TestClient) -> None:
    """Test /health endpoint returns status ok and version."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data
    assert "X-Request-ID" in response.headers


def test_api_v1_health_check(client: TestClient) -> None:
    """Test /api/v1/health endpoint returns status ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_readiness_check_returns_ready(client: TestClient) -> None:
    """Test /ready endpoint returns database connectivity status."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "uptime_seconds" in data
    assert data["components"]["database"]["status"] == "healthy"
