"""Tests for FastAPI server endpoints."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create test client with mocked Firestore restore."""
    with patch("memory.backup.restore_from_firestore", return_value={"status": "empty", "count": 0, "skipped": 0}):
        from server.main import app
        from starlette.testclient import TestClient
        return TestClient(app)


def test_health_endpoint(client):
    """GET /health returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["agent"] == "jazari"


def test_index_returns_html_or_status(client):
    """GET / returns either index.html or API status."""
    response = client.get("/")
    assert response.status_code == 200


def test_media_memory_missing_fields(client):
    """POST /api/media-memory with missing fields returns error."""
    response = client.post("/api/media-memory", json={})
    assert response.status_code == 200  # FastAPI returns 200 with error dict
    data = response.json()
    assert "error" in data


def test_media_memory_invalid_modality(client):
    """POST /api/media-memory with invalid modality returns error."""
    response = client.post("/api/media-memory", json={
        "user_id": "test",
        "modality": "video",  # invalid
        "data": "dGVzdA==",  # base64 of "test"
    })
    data = response.json()
    assert "error" in data
    assert "Invalid modality" in data["error"]


def test_media_memory_invalid_base64(client):
    """POST /api/media-memory with invalid base64 returns error."""
    response = client.post("/api/media-memory", json={
        "user_id": "test",
        "modality": "image",
        "data": "not-valid-base64!!!",
    })
    data = response.json()
    assert "error" in data
