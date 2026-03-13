"""Integration tests — end-to-end memory flow with mocked APIs."""

import pytest
import numpy as np
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta


FAKE_VECTOR = np.random.rand(768).astype(np.float32).tolist()


def _mock_embed_response():
    mock = MagicMock()
    embedding = MagicMock()
    embedding.values = FAKE_VECTOR
    mock.embeddings = [embedding]
    return mock


@pytest.fixture
def memory_store(tmp_path):
    """Create a MemoryStore with mocked Gemini API."""
    with patch("memory.store.genai") as mock_genai:
        mock_client = MagicMock()
        # Mock the async embed_content path (client.aio.models.embed_content)
        mock_client.aio.models.embed_content = AsyncMock(return_value=_mock_embed_response())
        mock_genai.Client.return_value = mock_client

        from memory.store import MemoryStore
        store = MemoryStore(db_path=str(tmp_path / "integration_db"))
        yield store


@pytest.mark.asyncio
async def test_full_lifecycle(memory_store):
    """Store → Search → Decay → Forget lifecycle."""
    user = "integration_user"

    # 1. Store a high-importance goal
    with patch("memory.store.score_importance", new_callable=AsyncMock, return_value=0.9):
        result = await memory_store.store(
            user_id=user, content="Run a marathon by December", memory_type="goal"
        )
        assert result["importance"] == 0.9
        goal_id = result["memory_id"]

    # 2. Store a low-importance observation
    with patch("memory.store.score_importance", new_callable=AsyncMock, return_value=0.15):
        await memory_store.store(
            user_id=user, content="It was sunny today", memory_type="event"
        )

    # 3. Search should find both
    results = await memory_store.search(user_id=user, query="marathon", limit=10)
    assert len(results) == 2

    # 4. Age the low-importance memory (simulate 45 days)
    import lancedb
    db = lancedb.connect(memory_store.db_path)
    table = db.open_table("memories")
    df = table.to_pandas()
    old = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    mask = df["content"].str.contains("sunny")
    df.loc[mask, "last_accessed"] = old
    db.create_table("memories", df, mode="overwrite")

    # 5. Search again — low-importance should be forgotten
    results = await memory_store.search(user_id=user, query="weather sunny", limit=10)
    contents = [r["content"] for r in results]
    assert "It was sunny today" not in contents  # Forgotten

    # 6. Goal should still be found (high importance persists)
    results = await memory_store.search(user_id=user, query="marathon running", limit=10)
    assert len(results) >= 1
    assert any("marathon" in r["content"].lower() for r in results)


@pytest.mark.asyncio
async def test_decaying_goals(memory_store):
    """Proactive coaching — detect decaying goals."""
    user = "goal_user"

    # Store a goal
    with patch("memory.store.score_importance", new_callable=AsyncMock, return_value=0.8):
        await memory_store.store(
            user_id=user, content="Lose 5kg by summer", memory_type="goal"
        )

    # Age it 20 days
    import lancedb
    db = lancedb.connect(memory_store.db_path)
    table = db.open_table("memories")
    df = table.to_pandas()
    old = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
    df["last_accessed"] = old
    db.create_table("memories", df, mode="overwrite")

    # Check decaying goals
    decaying = await memory_store.get_decaying_goals(user_id=user, threshold=0.4)
    assert len(decaying) >= 1
    assert "5kg" in decaying[0]["content"]
    assert decaying[0]["days_since_accessed"] >= 19


@pytest.mark.asyncio
async def test_multiuser_isolation(memory_store):
    """Ensure user memories are fully isolated."""
    with patch("memory.store.score_importance", new_callable=AsyncMock, return_value=0.8):
        await memory_store.store(user_id="alice", content="Alice loves cats", memory_type="fact")
        await memory_store.store(user_id="bob", content="Bob loves dogs", memory_type="fact")

    alice_results = await memory_store.search(user_id="alice", query="pets animals", limit=10)
    bob_results = await memory_store.search(user_id="bob", query="pets animals", limit=10)

    alice_contents = [r["content"] for r in alice_results]
    bob_contents = [r["content"] for r in bob_results]

    assert "Alice loves cats" in alice_contents
    assert "Bob loves dogs" not in alice_contents
    assert "Bob loves dogs" in bob_contents
    assert "Alice loves cats" not in bob_contents
