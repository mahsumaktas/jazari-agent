"""Finance tracking tools for Finance Agent."""

from datetime import datetime, timezone, timedelta
from tools.firestore_client import get_user_ref


def log_expense(user_id: str, amount: float, category: str, note: str = "") -> dict:
    """Log an expense.

    Args:
        user_id: The user's unique identifier.
        amount: Expense amount in user's currency.
        category: Category (e.g., "food", "transport", "entertainment").
        note: Optional description.

    Returns:
        dict with confirmation and expense_id.
    """
    ref = get_user_ref(user_id).collection("expenses").document()
    expense = {
        "amount": amount,
        "category": category.lower(),
        "note": note,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ref.set(expense)
    return {"message": f"Logged: {amount} ({category})", "expense_id": ref.id}


def set_budget(user_id: str, category: str, monthly_limit: float) -> dict:
    """Set a monthly budget for a category.

    Args:
        user_id: The user's unique identifier.
        category: Spending category.
        monthly_limit: Maximum monthly spending for this category.

    Returns:
        dict with confirmation.
    """
    ref = get_user_ref(user_id).collection("budgets").document(category.lower())
    ref.set({"category": category.lower(), "monthly_limit": monthly_limit}, merge=True)
    return {"message": f"Budget set: {category} = {monthly_limit}/month"}


def spending_summary(user_id: str, days: int = 30) -> dict:
    """Get spending summary for the last N days.

    Args:
        user_id: The user's unique identifier.
        days: Number of days to look back (default 30).

    Returns:
        dict with total, by-category breakdown.
    """
    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
    expenses = (
        get_user_ref(user_id)
        .collection("expenses")
        .where("date", ">=", cutoff)
        .stream()
    )
    by_category = {}
    total = 0
    for e in expenses:
        data = e.to_dict()
        cat = data["category"]
        amt = data["amount"]
        by_category[cat] = by_category.get(cat, 0) + amt
        total += amt

    return {
        "total": total,
        "by_category": by_category,
        "period_days": days,
    }
