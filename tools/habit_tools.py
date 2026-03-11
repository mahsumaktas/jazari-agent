"""Habit tracking tools for Discipline and Health Agents."""

from datetime import datetime, timezone, timedelta
from tools.firestore_client import get_user_ref


def create_habit(user_id: str, name: str, frequency: str = "daily") -> dict:
    """Create a new habit to track.

    Args:
        user_id: The user's unique identifier.
        name: Habit name (e.g., "Read 30 minutes").
        frequency: How often — "daily" or "weekly".

    Returns:
        dict with habit_id and confirmation.
    """
    ref = get_user_ref(user_id).collection("habits").document()
    habit = {
        "name": name,
        "frequency": frequency,
        "streak": 0,
        "best_streak": 0,
        "last_logged": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ref.set(habit)
    return {"habit_id": ref.id, "message": f"Habit created: {name} ({frequency})"}


def log_habit(user_id: str, habit_id: str) -> dict:
    """Log that a habit was completed today.

    Args:
        user_id: The user's unique identifier.
        habit_id: The habit document ID.

    Returns:
        dict with updated streak info.
    """
    ref = get_user_ref(user_id).collection("habits").document(habit_id)
    doc = ref.get()
    if not doc.exists:
        return {"error": "Habit not found"}

    data = doc.to_dict()
    today = datetime.now(timezone.utc).date().isoformat()
    last = data.get("last_logged")

    if last == today:
        return {"message": "Already logged today!", "streak": data["streak"]}

    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    if last == yesterday:
        new_streak = data["streak"] + 1
    else:
        new_streak = 1

    best = max(data.get("best_streak", 0), new_streak)
    ref.update({"streak": new_streak, "best_streak": best, "last_logged": today})
    return {"message": f"Logged! Streak: {new_streak} days", "streak": new_streak, "best_streak": best}


def habit_streak(user_id: str) -> dict:
    """Get all habits with their current streaks.

    Args:
        user_id: The user's unique identifier.

    Returns:
        dict with list of habits and streaks.
    """
    habits = get_user_ref(user_id).collection("habits").stream()
    result = []
    for h in habits:
        data = h.to_dict()
        result.append({
            "habit_id": h.id,
            "name": data["name"],
            "streak": data["streak"],
            "best_streak": data.get("best_streak", 0),
            "last_logged": data.get("last_logged"),
        })
    return {"habits": result}


def accountability_check(user_id: str) -> dict:
    """Check which habits were NOT done today — for tough love feedback.

    Args:
        user_id: The user's unique identifier.

    Returns:
        dict with missed and completed habits for today.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    habits = get_user_ref(user_id).collection("habits").stream()
    done = []
    missed = []
    for h in habits:
        data = h.to_dict()
        if data.get("last_logged") == today:
            done.append(data["name"])
        else:
            missed.append(data["name"])
    return {"done_today": done, "missed_today": missed, "completion_rate": f"{len(done)}/{len(done) + len(missed)}"}
