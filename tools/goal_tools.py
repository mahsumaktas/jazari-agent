"""Goal tracking tools for Career Agent."""

from datetime import datetime, timezone
from tools.firestore_client import get_user_ref


def set_career_goal(user_id: str, title: str, deadline: str = None, milestones: list[str] = None) -> dict:
    """Set a new career goal for the user.

    Args:
        user_id: The user's unique identifier.
        title: Goal title (e.g., "Learn Python basics").
        deadline: Optional deadline in YYYY-MM-DD format.
        milestones: Optional list of milestone descriptions.

    Returns:
        dict with goal_id and confirmation message.
    """
    ref = get_user_ref(user_id).collection("goals").document()
    goal = {
        "domain": "career",
        "title": title,
        "status": "active",
        "milestones": [{"text": m, "done": False} for m in (milestones or [])],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deadline": deadline,
    }
    ref.set(goal)
    return {"goal_id": ref.id, "message": f"Goal set: {title}"}


def track_milestone(user_id: str, goal_id: str, milestone_index: int) -> dict:
    """Mark a milestone as completed.

    Args:
        user_id: The user's unique identifier.
        goal_id: The goal document ID.
        milestone_index: Zero-based index of the milestone to mark done.

    Returns:
        dict with updated milestone status.
    """
    ref = get_user_ref(user_id).collection("goals").document(goal_id)
    doc = ref.get()
    if not doc.exists:
        return {"error": "Goal not found"}
    data = doc.to_dict()
    milestones = data.get("milestones", [])
    if 0 <= milestone_index < len(milestones):
        milestones[milestone_index]["done"] = True
        ref.update({"milestones": milestones})
        return {"message": f"Milestone {milestone_index + 1} completed!", "milestones": milestones}
    return {"error": "Invalid milestone index"}


def review_progress(user_id: str) -> dict:
    """Review all active career goals and their progress.

    Args:
        user_id: The user's unique identifier.

    Returns:
        dict with list of active goals and completion stats.
    """
    goals_ref = get_user_ref(user_id).collection("goals")
    goals = goals_ref.where("domain", "==", "career").where("status", "==", "active").stream()
    result = []
    for g in goals:
        data = g.to_dict()
        milestones = data.get("milestones", [])
        done = sum(1 for m in milestones if m.get("done"))
        result.append({
            "goal_id": g.id,
            "title": data["title"],
            "milestones_done": done,
            "milestones_total": len(milestones),
            "deadline": data.get("deadline"),
        })
    return {"goals": result, "total_active": len(result)}
