"""Persistent memory store for Jazari. Saves to JSON file, survives restarts."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

MEMORY_FILE = Path(__file__).parent.parent / "data" / "memories.json"


def _load() -> dict:
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {}


def _save(data: dict):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def store_memory(user_id: str, memory_type: str, content: str, importance: float = 0.5) -> dict:
    """Store a memory about the user. Persists across server restarts.

    Args:
        user_id: The user's unique identifier.
        memory_type: One of: fact, goal, event, preference, insight, habit.
        content: The memory content (e.g., "User goes to gym 3 days a week").
        importance: How important this memory is (0.0 to 1.0).

    Returns:
        dict with confirmation message.
    """
    memories = _load()
    if user_id not in memories:
        memories[user_id] = []

    memory = {
        "type": memory_type,
        "content": content,
        "importance": importance,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    memories[user_id].append(memory)
    _save(memories)
    return {"status": "stored", "message": f"Remembered: {content}"}


def recall_memories(user_id: str, query: str = "", limit: int = 10) -> dict:
    """Search user's memories. Returns all if no query, or filters by keyword match.

    Args:
        user_id: The user's unique identifier.
        query: Optional search keyword — matches against memory content.
        limit: Maximum number of results.

    Returns:
        dict with matching memories sorted by importance.
    """
    memories = _load()
    user_mems = memories.get(user_id, [])

    if query:
        q = query.lower()
        results = [m for m in user_mems if q in m["content"].lower()]
    else:
        results = list(user_mems)

    results.sort(key=lambda m: m["importance"], reverse=True)
    return {"memories": results[:limit], "total": len(user_mems)}
