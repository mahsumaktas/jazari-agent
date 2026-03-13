"""Tests for memory_tools wrapper functions."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


async def test_store_memory_success():
    """store_memory should return result from MemoryStore."""
    mock_store = MagicMock()
    mock_store.store = AsyncMock(return_value={
        "memory_id": "test-123",
        "content": "User's name is Ali",
        "importance": 0.9,
        "modality": "text",
        "message": "Remembered: User's name is Ali...",
    })

    with patch("tools.memory_tools._get_store", return_value=mock_store):
        from tools.memory_tools import store_memory
        result = await store_memory(user_id="u1", memory_type="fact", content="User's name is Ali")

    assert result["memory_id"] == "test-123"
    assert result["importance"] == 0.9


async def test_store_memory_error_handling():
    """store_memory should return graceful error on exception."""
    mock_store = MagicMock()
    mock_store.store = AsyncMock(side_effect=ConnectionError("Network down"))

    with patch("tools.memory_tools._get_store", return_value=mock_store):
        from tools.memory_tools import store_memory
        result = await store_memory(user_id="u1", memory_type="fact", content="test")

    assert "error" in result
    assert "ConnectionError" in result["error"]


async def test_search_memory_success():
    """search_memory should return memories and count."""
    mock_store = MagicMock()
    mock_store.search = AsyncMock(return_value=[
        {"content": "User likes running", "importance": 0.7},
    ])

    with patch("tools.memory_tools._get_store", return_value=mock_store):
        from tools.memory_tools import search_memory
        result = await search_memory(user_id="u1", query="hobbies")

    assert result["count"] == 1
    assert result["memories"][0]["content"] == "User likes running"


async def test_search_memory_error_returns_empty():
    """search_memory should return empty on error, not crash."""
    mock_store = MagicMock()
    mock_store.search = AsyncMock(side_effect=RuntimeError("DB error"))

    with patch("tools.memory_tools._get_store", return_value=mock_store):
        from tools.memory_tools import search_memory
        result = await search_memory(user_id="u1", query="anything")

    assert result["count"] == 0
    assert result["memories"] == []


async def test_get_decaying_goals_error_returns_empty():
    """get_decaying_goals should return empty on error."""
    mock_store = MagicMock()
    mock_store.get_decaying_goals = AsyncMock(side_effect=RuntimeError("fail"))

    with patch("tools.memory_tools._get_store", return_value=mock_store):
        from tools.memory_tools import get_decaying_goals
        result = await get_decaying_goals(user_id="u1")

    assert result["count"] == 0
    assert result["decaying_goals"] == []


async def test_save_conversation_summary():
    """save_conversation_summary should store insight memory."""
    mock_store = MagicMock()
    mock_store.store = AsyncMock(return_value={"memory_id": "sum-1"})

    with patch("tools.memory_tools._get_store", return_value=mock_store):
        from tools.memory_tools import save_conversation_summary
        result = await save_conversation_summary(
            user_id="u1",
            summary="Discussed career goals",
            key_points="promotion, skills, timeline",
        )

    assert result["memory_id"] == "sum-1"
    call_args = mock_store.store.call_args
    assert "Session summary" in call_args.kwargs["content"]
    assert call_args.kwargs["memory_type"] == "insight"
