"""Memory tools for Jazari agents — semantic search via MemoryStore."""

from memory.store import MemoryStore

_store: MemoryStore | None = None


def _get_store() -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store


async def store_memory(user_id: str, memory_type: str, content: str) -> dict:
    """Store a new memory about the user with automatic importance scoring.

    Args:
        user_id: The user's unique identifier.
        memory_type: One of: fact, goal, event, preference, insight.
        content: The memory content (e.g., "User's name is Mehmet").

    Returns:
        dict with memory_id and confirmation message.
    """
    try:
        store = _get_store()
        return await store.store(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
        )
    except Exception as e:
        return {"error": f"Failed to store memory: {type(e).__name__}", "message": "I'll remember this for now but couldn't persist it."}


async def search_memory(user_id: str, query: str, limit: int = 5) -> dict:
    """Search user's memories using semantic similarity.

    Args:
        user_id: The user's unique identifier.
        query: Natural language search query.
        limit: Maximum number of results.

    Returns:
        dict with matching memories ranked by relevance and importance.
    """
    try:
        store = _get_store()
        results = await store.search(user_id=user_id, query=query, limit=limit)
        return {"memories": results, "count": len(results)}
    except Exception:
        return {"memories": [], "count": 0, "note": "Memory search unavailable, starting fresh."}


async def store_media_memory(
    user_id: str,
    memory_type: str,
    content: str,
    media_bytes: bytes,
    modality: str,
    media_uri: str = "",
) -> dict:
    """Store a photo or voice note memory with multimodal embedding.

    Args:
        user_id: The user's unique identifier.
        memory_type: visual or audio.
        content: Optional text description.
        media_bytes: Raw image (JPEG) or audio (WAV) bytes.
        modality: image or audio.
        media_uri: GCS URI if media was uploaded.

    Returns:
        dict with memory_id and generated description.
    """
    try:
        store = _get_store()
        return await store.store(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            modality=modality,
            media_bytes=media_bytes,
            media_uri=media_uri,
        )
    except Exception as e:
        return {"error": f"Failed to store media memory: {type(e).__name__}", "message": "Media received but couldn't persist it."}


async def get_decaying_goals(user_id: str) -> dict:
    """Find goals and habits the user hasn't mentioned recently.

    Used for proactive coaching: follow up on forgotten goals.

    Args:
        user_id: The user's unique identifier.

    Returns:
        dict with decaying goals/habits and days since last mention.
    """
    try:
        store = _get_store()
        decaying = await store.get_decaying_goals(user_id=user_id)
        return {"decaying_goals": decaying, "count": len(decaying)}
    except Exception:
        return {"decaying_goals": [], "count": 0}


async def save_conversation_summary(user_id: str, summary: str, key_points: str) -> dict:
    """Save a conversation summary at the end of a session.

    Args:
        user_id: The user's unique identifier.
        summary: 1-2 sentence summary of the conversation.
        key_points: Comma-separated key points discussed.

    Returns:
        dict with confirmation.
    """
    try:
        store = _get_store()
        return await store.store(
            user_id=user_id,
            content=f"Session summary: {summary}. Key points: {key_points}",
            memory_type="insight",
        )
    except Exception:
        return {"message": "Summary noted but not persisted."}


def get_user_profile(user_id: str) -> dict:
    """Get a summary of everything known about the user.

    Args:
        user_id: The user's unique identifier.

    Returns:
        dict with user profile from Firestore.
    """
    from tools.firestore_client import get_user_ref
    from google.cloud import firestore

    user_ref = get_user_ref(user_id)
    profile_doc = user_ref.get()
    profile = profile_doc.to_dict() if profile_doc.exists else {}

    goals = user_ref.collection("goals").where("status", "==", "active").stream()
    goal_count = sum(1 for _ in goals)

    habits = user_ref.collection("habits").stream()
    habit_list = [{"name": h.to_dict()["name"], "streak": h.to_dict()["streak"]} for h in habits]

    return {
        "profile": profile,
        "active_goals": goal_count,
        "habits": habit_list,
    }
