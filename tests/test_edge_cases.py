"""Edge case and security tests."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import numpy as np

FAKE_VECTOR = np.random.rand(768).astype(np.float32).tolist()


def _mock_embed_response():
    mock = MagicMock()
    embedding = MagicMock()
    embedding.values = FAKE_VECTOR
    mock.embeddings = [embedding]
    return mock


@pytest.fixture
def memory_store(tmp_path):
    with patch("memory.store.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.aio.models.embed_content = AsyncMock(return_value=_mock_embed_response())
        mock_genai.Client.return_value = mock_client
        from memory.store import MemoryStore
        store = MemoryStore(db_path=str(tmp_path / "edge_db"))
        yield store


@pytest.mark.parametrize("content", [
    "",
    "   ",
    "A" * 10000,
    "Test with emoji \U0001f3af\U0001f525\U0001f4aa",
    "T\u00fcrk\u00e7e karakter: \u015f\u00e7\u0131\u011f\u00fc\u00f6",
    "\u0645\u0631\u062d\u0628\u0627 \u0628\u0643",
])
async def test_store_handles_special_content(memory_store, content):
    """Store should handle various text inputs without crashing."""
    with patch("memory.store.score_importance", new_callable=AsyncMock, return_value=0.5):
        with patch("memory.backup.backup_single_record", new_callable=AsyncMock):
            result = await memory_store.store(
                user_id="test_user", content=content, memory_type="fact"
            )
            assert "memory_id" in result


async def test_search_nonexistent_user(memory_store):
    """Search for user with no memories returns empty list."""
    results = await memory_store.search(user_id="ghost_user", query="anything", limit=5)
    assert results == []


async def test_store_and_search_turkish(memory_store):
    """Turkish text should be storable and searchable."""
    with patch("memory.store.score_importance", new_callable=AsyncMock, return_value=0.9):
        with patch("memory.backup.backup_single_record", new_callable=AsyncMock):
            await memory_store.store(
                user_id="tr_user",
                content="Spor yapmak istiyorum, haftada 3 g\u00fcn ko\u015fu",
                memory_type="goal",
            )
    results = await memory_store.search(user_id="tr_user", query="egzersiz ko\u015fu", limit=5)
    assert len(results) >= 1


async def test_sql_injection_in_user_id(memory_store):
    """SQL injection attempt in user_id should not crash or leak data."""
    with patch("memory.store.score_importance", new_callable=AsyncMock, return_value=0.5):
        with patch("memory.backup.backup_single_record", new_callable=AsyncMock):
            await memory_store.store(
                user_id="safe_user", content="Secret data", memory_type="fact"
            )

    # Attempt injection
    malicious_ids = [
        "'; DROP TABLE memories; --",
        "user' OR '1'='1",
        "user\"; SELECT * FROM memories; --",
    ]
    for mal_id in malicious_ids:
        results = await memory_store.search(user_id=mal_id, query="secret", limit=5)
        # Should return empty, NOT crash or return other users' data
        assert isinstance(results, list)
        for r in results:
            assert r.get("content") != "Secret data"
