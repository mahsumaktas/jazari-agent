"""WebSocket and input validation tests.

Covers WebSocket-specific validation (empty message, oversized message,
invalid JSON, media size guard) and the REST oversized-upload path that
existing test_server.py does not exercise.
"""
import pytest
import base64
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock

import os
os.environ.setdefault("GOOGLE_API_KEY", "test-key")

with patch("memory.backup.restore_from_firestore", return_value={"status": "empty", "count": 0, "skipped": 0}):
    from server.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _empty_gen():
    """Async generator that yields nothing (no greeting sent)."""
    return
    yield  # noqa: unreachable — makes this a generator


async def _single_gen(event):
    yield event


def _make_mock_event(text="Hello", author="jazari"):
    ev = MagicMock()
    ev.is_final_response.return_value = True
    part = MagicMock()
    part.text = text
    ev.content = MagicMock()
    ev.content.parts = [part]
    ev.author = author
    return ev


# ---------------------------------------------------------------------------
# REST: oversized upload (not covered in test_server.py)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_media_memory_rejects_oversized():
    """POST /api/media-memory rejects payloads exceeding 50 MB."""
    large_data = base64.b64encode(b"x" * (51 * 1024 * 1024)).decode()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/media-memory", json={
            "user_id": "test",
            "modality": "image",
            "data": large_data,
        })
    data = resp.json()
    assert "error" in data
    assert "large" in data["error"].lower() or "too" in data["error"].lower()


# ---------------------------------------------------------------------------
# WebSocket /ws — text validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ws_rejects_invalid_json():
    """WebSocket returns error for non-JSON text frames."""
    with patch("server.main.text_runner") as mock_runner:
        # Mock returns empty iter => no greeting sent, no receive needed
        mock_runner.run_async = MagicMock(return_value=_empty_gen())

        from starlette.testclient import TestClient
        with TestClient(app) as client:
            with client.websocket_connect("/ws?userId=test") as ws:
                ws.send_text("this is not json")
                resp = ws.receive_json()
                assert resp["type"] == "error"
                assert "invalid" in resp["content"].lower() or "format" in resp["content"].lower()


@pytest.mark.asyncio
async def test_ws_rejects_empty_message():
    """WebSocket returns error for empty text content."""
    with patch("server.main.text_runner") as mock_runner:
        mock_runner.run_async = MagicMock(return_value=_empty_gen())

        from starlette.testclient import TestClient
        with TestClient(app) as client:
            with client.websocket_connect("/ws?userId=test") as ws:
                ws.send_json({"type": "text", "content": "   "})
                resp = ws.receive_json()
                assert resp["type"] == "error"
                assert "empty" in resp["content"].lower()


@pytest.mark.asyncio
async def test_ws_rejects_oversized_message():
    """WebSocket returns error for messages exceeding 10 000 chars."""
    with patch("server.main.text_runner") as mock_runner:
        mock_runner.run_async = MagicMock(return_value=_empty_gen())

        from starlette.testclient import TestClient
        with TestClient(app) as client:
            with client.websocket_connect("/ws?userId=test") as ws:
                ws.send_json({"type": "text", "content": "A" * 10_001})
                resp = ws.receive_json()
                assert resp["type"] == "error"
                assert "long" in resp["content"].lower() or "10,000" in resp["content"]


@pytest.mark.asyncio
async def test_ws_media_rejects_oversized():
    """WebSocket media handler rejects payloads exceeding MAX_UPLOAD_BYTES."""
    with patch("server.main.text_runner") as mock_runner:
        mock_runner.run_async = MagicMock(return_value=_empty_gen())

        large_b64 = base64.b64encode(b"x" * (51 * 1024 * 1024)).decode()

        from starlette.testclient import TestClient
        with TestClient(app) as client:
            with client.websocket_connect("/ws?userId=test") as ws:
                ws.send_json({
                    "type": "media",
                    "modality": "image",
                    "data": large_b64,
                })
                resp = ws.receive_json()
                assert resp["type"] == "error"
                assert "large" in resp["content"].lower() or "too" in resp["content"].lower()


@pytest.mark.asyncio
async def test_ws_accepts_valid_text():
    """WebSocket returns agent response for a valid text message."""
    mock_event = _make_mock_event(text="Hello from Jazari", author="jazari")

    # Patch types.Content and types.Part.from_text so the real Gemini SDK
    # doesn't crash when constructing the message content.
    mock_types = MagicMock()

    with (
        patch("server.main.text_runner") as mock_runner,
        patch("server.main.types", mock_types),
    ):
        call_count = {"n": 0}

        def _run_async(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # greeting call => empty
                return _empty_gen()
            # actual message => return event
            return _single_gen(mock_event)

        mock_runner.run_async = MagicMock(side_effect=_run_async)

        from starlette.testclient import TestClient
        with TestClient(app) as client:
            with client.websocket_connect("/ws?userId=test") as ws:
                ws.send_json({"type": "text", "content": "Hello"})
                resp = ws.receive_json()
                assert resp["type"] == "text"
                assert resp["content"] == "Hello from Jazari"
                assert resp["agent"] == "jazari"
