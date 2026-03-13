"""Tests for finance, goal, and habit tools."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta


# ===== Finance Tools =====


@patch("tools.finance_tools.get_user_ref")
def test_log_expense_returns_dict(mock_ref):
    """log_expense returns a confirmation dict with message and expense_id."""
    from tools.finance_tools import log_expense

    mock_doc = MagicMock()
    mock_doc.id = "exp-001"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    result = log_expense(user_id="test", amount=42.50, category="food", note="lunch")
    assert isinstance(result, dict)
    assert result["expense_id"] == "exp-001"
    assert "42.5" in result["message"]
    assert "food" in result["message"]
    mock_doc.set.assert_called_once()


@patch("tools.finance_tools.get_user_ref")
def test_log_expense_lowercases_category(mock_ref):
    """log_expense normalizes category to lowercase."""
    from tools.finance_tools import log_expense

    mock_doc = MagicMock()
    mock_doc.id = "exp-002"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    log_expense(user_id="test", amount=10, category="FOOD")
    saved = mock_doc.set.call_args[0][0]
    assert saved["category"] == "food"


@patch("tools.finance_tools.get_user_ref")
def test_log_expense_stores_date_fields(mock_ref):
    """log_expense stores date and created_at in the expense doc."""
    from tools.finance_tools import log_expense

    mock_doc = MagicMock()
    mock_doc.id = "exp-003"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    log_expense(user_id="test", amount=5, category="coffee")
    saved = mock_doc.set.call_args[0][0]
    assert "date" in saved
    assert "created_at" in saved
    assert saved["note"] == ""


@patch("tools.finance_tools.get_user_ref")
def test_set_budget_returns_dict(mock_ref):
    """set_budget returns a confirmation dict."""
    from tools.finance_tools import set_budget

    mock_doc = MagicMock()
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    result = set_budget(user_id="test", category="food", monthly_limit=500.0)
    assert isinstance(result, dict)
    assert "500" in result["message"]
    mock_doc.set.assert_called_once()


@patch("tools.finance_tools.get_user_ref")
def test_set_budget_merges(mock_ref):
    """set_budget uses merge=True to avoid overwriting."""
    from tools.finance_tools import set_budget

    mock_doc = MagicMock()
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    set_budget(user_id="test", category="transport", monthly_limit=200.0)
    call_kwargs = mock_doc.set.call_args
    assert call_kwargs[1]["merge"] is True


@patch("tools.finance_tools.get_user_ref")
def test_spending_summary_empty(mock_ref):
    """spending_summary returns zero total when no expenses exist."""
    from tools.finance_tools import spending_summary

    mock_collection = MagicMock()
    mock_collection.where.return_value.stream.return_value = []
    mock_ref.return_value.collection.return_value = mock_collection

    result = spending_summary(user_id="test", days=30)
    assert isinstance(result, dict)
    assert result["total"] == 0
    assert result["by_category"] == {}
    assert result["period_days"] == 30


@patch("tools.finance_tools.get_user_ref")
def test_spending_summary_aggregates(mock_ref):
    """spending_summary correctly sums expenses by category."""
    from tools.finance_tools import spending_summary

    mock_exp1 = MagicMock()
    mock_exp1.to_dict.return_value = {"category": "food", "amount": 25.0}
    mock_exp2 = MagicMock()
    mock_exp2.to_dict.return_value = {"category": "food", "amount": 15.0}
    mock_exp3 = MagicMock()
    mock_exp3.to_dict.return_value = {"category": "transport", "amount": 10.0}

    mock_collection = MagicMock()
    mock_collection.where.return_value.stream.return_value = [mock_exp1, mock_exp2, mock_exp3]
    mock_ref.return_value.collection.return_value = mock_collection

    result = spending_summary(user_id="test", days=7)
    assert result["total"] == 50.0
    assert result["by_category"]["food"] == 40.0
    assert result["by_category"]["transport"] == 10.0
    assert result["period_days"] == 7


@patch("tools.finance_tools.get_user_ref")
def test_spending_summary_default_days(mock_ref):
    """spending_summary defaults to 30 days."""
    from tools.finance_tools import spending_summary

    mock_collection = MagicMock()
    mock_collection.where.return_value.stream.return_value = []
    mock_ref.return_value.collection.return_value = mock_collection

    result = spending_summary(user_id="test")
    assert result["period_days"] == 30


# ===== Goal Tools =====


@patch("tools.goal_tools.get_user_ref")
def test_set_career_goal_returns_dict(mock_ref):
    """set_career_goal creates a goal and returns goal_id + message."""
    from tools.goal_tools import set_career_goal

    mock_doc = MagicMock()
    mock_doc.id = "goal-001"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    result = set_career_goal(user_id="test", title="Learn Python")
    assert isinstance(result, dict)
    assert result["goal_id"] == "goal-001"
    assert "Learn Python" in result["message"]
    mock_doc.set.assert_called_once()


@patch("tools.goal_tools.get_user_ref")
def test_set_career_goal_without_milestones(mock_ref):
    """set_career_goal stores empty milestones when none provided."""
    from tools.goal_tools import set_career_goal

    mock_doc = MagicMock()
    mock_doc.id = "goal-no-ms"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    set_career_goal(user_id="test", title="Simple goal")
    saved = mock_doc.set.call_args[0][0]
    assert saved["milestones"] == []
    assert saved["deadline"] is None


@patch("tools.goal_tools.get_user_ref")
def test_set_career_goal_with_milestones(mock_ref):
    """set_career_goal stores milestones as list of {text, done} dicts."""
    from tools.goal_tools import set_career_goal

    mock_doc = MagicMock()
    mock_doc.id = "goal-002"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    set_career_goal(
        user_id="test",
        title="Learn Python",
        milestones=["Basics", "OOP", "Projects"],
    )
    saved = mock_doc.set.call_args[0][0]
    assert len(saved["milestones"]) == 3
    assert saved["milestones"][0] == {"text": "Basics", "done": False}
    assert saved["milestones"][2] == {"text": "Projects", "done": False}
    assert saved["domain"] == "career"
    assert saved["status"] == "active"


@patch("tools.goal_tools.get_user_ref")
def test_set_career_goal_with_deadline(mock_ref):
    """set_career_goal stores the deadline."""
    from tools.goal_tools import set_career_goal

    mock_doc = MagicMock()
    mock_doc.id = "goal-003"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    set_career_goal(user_id="test", title="Get cert", deadline="2026-12-31")
    saved = mock_doc.set.call_args[0][0]
    assert saved["deadline"] == "2026-12-31"


@patch("tools.goal_tools.get_user_ref")
def test_track_milestone_success(mock_ref):
    """track_milestone marks the correct milestone as done."""
    from tools.goal_tools import track_milestone

    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {
        "milestones": [
            {"text": "Step 1", "done": False},
            {"text": "Step 2", "done": False},
        ]
    }
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc_ref

    result = track_milestone(user_id="test", goal_id="goal-001", milestone_index=0)
    assert isinstance(result, dict)
    assert "Milestone 1 completed" in result["message"]
    assert result["milestones"][0]["done"] is True
    assert result["milestones"][1]["done"] is False
    mock_doc_ref.update.assert_called_once()


@patch("tools.goal_tools.get_user_ref")
def test_track_milestone_not_found(mock_ref):
    """track_milestone returns error when goal does not exist."""
    from tools.goal_tools import track_milestone

    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = False
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc_ref

    result = track_milestone(user_id="test", goal_id="bad-id", milestone_index=0)
    assert "error" in result
    assert "not found" in result["error"]


@patch("tools.goal_tools.get_user_ref")
def test_track_milestone_invalid_index(mock_ref):
    """track_milestone returns error for out-of-range index."""
    from tools.goal_tools import track_milestone

    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {
        "milestones": [{"text": "Only one", "done": False}]
    }
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc_ref

    result = track_milestone(user_id="test", goal_id="goal-001", milestone_index=5)
    assert "error" in result
    assert "Invalid" in result["error"]


@patch("tools.goal_tools.get_user_ref")
def test_review_progress_empty(mock_ref):
    """review_progress returns empty list when no active goals."""
    from tools.goal_tools import review_progress

    mock_collection = MagicMock()
    mock_collection.where.return_value.where.return_value.stream.return_value = []
    mock_ref.return_value.collection.return_value = mock_collection

    result = review_progress(user_id="test")
    assert isinstance(result, dict)
    assert result["goals"] == []
    assert result["total_active"] == 0


@patch("tools.goal_tools.get_user_ref")
def test_review_progress_with_goals(mock_ref):
    """review_progress computes milestone completion stats."""
    from tools.goal_tools import review_progress

    mock_goal = MagicMock()
    mock_goal.id = "g1"
    mock_goal.to_dict.return_value = {
        "title": "Learn Go",
        "milestones": [
            {"text": "Basics", "done": True},
            {"text": "Web", "done": False},
        ],
        "deadline": "2026-06-01",
    }

    mock_collection = MagicMock()
    mock_collection.where.return_value.where.return_value.stream.return_value = [mock_goal]
    mock_ref.return_value.collection.return_value = mock_collection

    result = review_progress(user_id="test")
    assert result["total_active"] == 1
    assert result["goals"][0]["goal_id"] == "g1"
    assert result["goals"][0]["title"] == "Learn Go"
    assert result["goals"][0]["milestones_done"] == 1
    assert result["goals"][0]["milestones_total"] == 2
    assert result["goals"][0]["deadline"] == "2026-06-01"


# ===== Habit Tools =====


@patch("tools.habit_tools.get_user_ref")
def test_create_habit_returns_dict(mock_ref):
    """create_habit creates a new habit and returns habit_id + message."""
    from tools.habit_tools import create_habit

    mock_doc = MagicMock()
    mock_doc.id = "hab-001"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    result = create_habit(user_id="test", name="Morning run", frequency="daily")
    assert isinstance(result, dict)
    assert result["habit_id"] == "hab-001"
    assert "Morning run" in result["message"]
    mock_doc.set.assert_called_once()


@patch("tools.habit_tools.get_user_ref")
def test_create_habit_default_frequency(mock_ref):
    """create_habit defaults to daily frequency."""
    from tools.habit_tools import create_habit

    mock_doc = MagicMock()
    mock_doc.id = "hab-002"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    result = create_habit(user_id="test", name="Meditate")
    assert "daily" in result["message"]
    saved = mock_doc.set.call_args[0][0]
    assert saved["frequency"] == "daily"
    assert saved["streak"] == 0
    assert saved["best_streak"] == 0
    assert saved["last_logged"] is None


@patch("tools.habit_tools.get_user_ref")
def test_create_habit_weekly(mock_ref):
    """create_habit accepts weekly frequency."""
    from tools.habit_tools import create_habit

    mock_doc = MagicMock()
    mock_doc.id = "hab-003"
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc

    result = create_habit(user_id="test", name="Gym", frequency="weekly")
    assert "weekly" in result["message"]
    saved = mock_doc.set.call_args[0][0]
    assert saved["frequency"] == "weekly"


@patch("tools.habit_tools.get_user_ref")
def test_log_habit_not_found(mock_ref):
    """log_habit returns error when habit does not exist."""
    from tools.habit_tools import log_habit

    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = False
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc_ref

    result = log_habit(user_id="test", habit_id="bad-id")
    assert "error" in result
    assert "not found" in result["error"]


@patch("tools.habit_tools.get_user_ref")
def test_log_habit_already_logged_today(mock_ref):
    """log_habit returns 'already logged' when called twice same day."""
    from tools.habit_tools import log_habit

    today = datetime.now(timezone.utc).date().isoformat()
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {"last_logged": today, "streak": 5}
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc_ref

    result = log_habit(user_id="test", habit_id="hab-001")
    assert "Already logged" in result["message"]
    assert result["streak"] == 5
    # Should NOT call update since nothing changed
    mock_doc_ref.update.assert_not_called()


@patch("tools.habit_tools.get_user_ref")
def test_log_habit_continues_streak(mock_ref):
    """log_habit increments streak when logged on consecutive day."""
    from tools.habit_tools import log_habit

    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {
        "last_logged": yesterday,
        "streak": 3,
        "best_streak": 5,
    }
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc_ref

    result = log_habit(user_id="test", habit_id="hab-001")
    assert result["streak"] == 4
    assert result["best_streak"] == 5
    mock_doc_ref.update.assert_called_once()


@patch("tools.habit_tools.get_user_ref")
def test_log_habit_new_best_streak(mock_ref):
    """log_habit updates best_streak when current exceeds it."""
    from tools.habit_tools import log_habit

    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {
        "last_logged": yesterday,
        "streak": 9,
        "best_streak": 9,
    }
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc_ref

    result = log_habit(user_id="test", habit_id="hab-001")
    assert result["streak"] == 10
    assert result["best_streak"] == 10


@patch("tools.habit_tools.get_user_ref")
def test_log_habit_resets_streak(mock_ref):
    """log_habit resets streak to 1 when day was missed."""
    from tools.habit_tools import log_habit

    old_date = (datetime.now(timezone.utc).date() - timedelta(days=3)).isoformat()
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {
        "last_logged": old_date,
        "streak": 10,
        "best_streak": 10,
    }
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc_ref

    result = log_habit(user_id="test", habit_id="hab-001")
    assert result["streak"] == 1
    assert result["best_streak"] == 10


@patch("tools.habit_tools.get_user_ref")
def test_log_habit_first_ever_log(mock_ref):
    """log_habit starts streak at 1 when no previous log exists."""
    from tools.habit_tools import log_habit

    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {
        "last_logged": None,
        "streak": 0,
        "best_streak": 0,
    }
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_ref.return_value.collection.return_value.document.return_value = mock_doc_ref

    result = log_habit(user_id="test", habit_id="hab-001")
    assert result["streak"] == 1
    assert result["best_streak"] == 1


@patch("tools.habit_tools.get_user_ref")
def test_habit_streak_empty(mock_ref):
    """habit_streak returns empty list when no habits."""
    from tools.habit_tools import habit_streak

    mock_ref.return_value.collection.return_value.stream.return_value = []

    result = habit_streak(user_id="test")
    assert isinstance(result, dict)
    assert result["habits"] == []


@patch("tools.habit_tools.get_user_ref")
def test_habit_streak_with_habits(mock_ref):
    """habit_streak returns correct streak data for each habit."""
    from tools.habit_tools import habit_streak

    mock_h1 = MagicMock()
    mock_h1.id = "h1"
    mock_h1.to_dict.return_value = {
        "name": "Run",
        "streak": 5,
        "best_streak": 12,
        "last_logged": "2026-03-12",
    }
    mock_h2 = MagicMock()
    mock_h2.id = "h2"
    mock_h2.to_dict.return_value = {
        "name": "Read",
        "streak": 0,
        "best_streak": 3,
        "last_logged": None,
    }

    mock_ref.return_value.collection.return_value.stream.return_value = [mock_h1, mock_h2]

    result = habit_streak(user_id="test")
    assert len(result["habits"]) == 2
    assert result["habits"][0]["name"] == "Run"
    assert result["habits"][0]["streak"] == 5
    assert result["habits"][0]["habit_id"] == "h1"
    assert result["habits"][1]["best_streak"] == 3


@patch("tools.habit_tools.get_user_ref")
def test_accountability_check_empty(mock_ref):
    """accountability_check returns zeros when no habits exist."""
    from tools.habit_tools import accountability_check

    mock_ref.return_value.collection.return_value.stream.return_value = []

    result = accountability_check(user_id="test")
    assert isinstance(result, dict)
    assert result["done_today"] == []
    assert result["missed_today"] == []
    assert result["completion_rate"] == "0/0"


@patch("tools.habit_tools.get_user_ref")
def test_accountability_check_mixed(mock_ref):
    """accountability_check correctly splits done vs missed habits."""
    from tools.habit_tools import accountability_check

    today = datetime.now(timezone.utc).date().isoformat()

    mock_h1 = MagicMock()
    mock_h1.to_dict.return_value = {"name": "Run", "last_logged": today}
    mock_h2 = MagicMock()
    mock_h2.to_dict.return_value = {"name": "Read", "last_logged": "2026-01-01"}
    mock_h3 = MagicMock()
    mock_h3.to_dict.return_value = {"name": "Meditate", "last_logged": None}

    mock_ref.return_value.collection.return_value.stream.return_value = [mock_h1, mock_h2, mock_h3]

    result = accountability_check(user_id="test")
    assert result["done_today"] == ["Run"]
    assert set(result["missed_today"]) == {"Read", "Meditate"}
    assert result["completion_rate"] == "1/3"


@patch("tools.habit_tools.get_user_ref")
def test_accountability_check_all_done(mock_ref):
    """accountability_check shows full completion."""
    from tools.habit_tools import accountability_check

    today = datetime.now(timezone.utc).date().isoformat()

    mock_h1 = MagicMock()
    mock_h1.to_dict.return_value = {"name": "Run", "last_logged": today}
    mock_h2 = MagicMock()
    mock_h2.to_dict.return_value = {"name": "Read", "last_logged": today}

    mock_ref.return_value.collection.return_value.stream.return_value = [mock_h1, mock_h2]

    result = accountability_check(user_id="test")
    assert len(result["done_today"]) == 2
    assert result["missed_today"] == []
    assert result["completion_rate"] == "2/2"
