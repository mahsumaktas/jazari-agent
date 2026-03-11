"""Memory tools for Memory Agent — persistent cross-session knowledge."""

from datetime import datetime, timezone
from google.cloud import firestore
from tools.firestore_client import get_user_ref


def store_memory(user_id: str, memory_type: str, content: str, importance: float = 0.5) -> dict:
    """Store a new memory about the user.

    Args:
        user_id: The user's unique identifier.
        memory_type: One of: fact, goal, event, preference, insight.
        content: The memory content (e.g., "User's name is Mehmet").
        importance: How important this memory is (0.0 to 1.0).

    Returns:
        dict with memory_id and confirmation message.
    """
    ref = get_user_ref(user_id).collection("memories").document()
    memory = {
        "type": memory_type,
        "content": content,
        "importance": importance,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_accessed": datetime.now(timezone.utc).isoformat(),
        "access_count": 0,
    }
    ref.set(memory)
    return {"memory_id": ref.id, "message": f"Remembered: {content[:50]}..."}


def search_memory(user_id: str, query: str, limit: int = 5) -> dict:
    """Search user's memories by keyword matching.

    Args:
        user_id: The user's unique identifier.
        query: Search query — matches against memory content.
        limit: Maximum number of results.

    Returns:
        dict with matching memories sorted by importance.
    """
    memories_ref = get_user_ref(user_id).collection("memories")
    all_memories = memories_ref.order_by("importance", direction=firestore.Query.DESCENDING).stream()

    query_lower = query.lower()
    results = []
    for m in all_memories:
        data = m.to_dict()
        if query_lower in data.get("content", "").lower():
            results.append({
                "memory_id": m.id,
                "type": data["type"],
                "content": data["content"],
                "importance": data["importance"],
                "created_at": data["created_at"],
            })
            m.reference.update({
                "last_accessed": datetime.now(timezone.utc).isoformat(),
                "access_count": firestore.Increment(1),
            })
            if len(results) >= limit:
                break

    return {"memories": results, "count": len(results)}


def get_user_profile(user_id: str) -> dict:
    """Get a summary of everything known about the user.

    Args:
        user_id: The user's unique identifier.

    Returns:
        dict with user profile, active goals, habit streaks, and key memories.
    """
    user_ref = get_user_ref(user_id)

    profile_doc = user_ref.get()
    profile = profile_doc.to_dict() if profile_doc.exists else {}

    memories = (
        user_ref.collection("memories")
        .order_by("importance", direction=firestore.Query.DESCENDING)
        .limit(5)
        .stream()
    )
    key_memories = [{"type": m.to_dict()["type"], "content": m.to_dict()["content"]} for m in memories]

    goals = user_ref.collection("goals").where("status", "==", "active").stream()
    goal_count = sum(1 for _ in goals)

    habits = user_ref.collection("habits").stream()
    habit_list = [{"name": h.to_dict()["name"], "streak": h.to_dict()["streak"]} for h in habits]

    return {
        "profile": profile,
        "key_memories": key_memories,
        "active_goals": goal_count,
        "habits": habit_list,
    }


def get_recent_context(user_id: str, limit: int = 3) -> dict:
    """Get recent conversation summaries for context.

    Args:
        user_id: The user's unique identifier.
        limit: Number of recent conversations to retrieve.

    Returns:
        dict with recent conversation summaries.
    """
    convos = (
        get_user_ref(user_id)
        .collection("conversations")
        .order_by("date", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    result = []
    for c in convos:
        data = c.to_dict()
        result.append({
            "date": data.get("date"),
            "summary": data.get("summary"),
            "key_points": data.get("key_points", []),
        })
    return {"recent_conversations": result}
