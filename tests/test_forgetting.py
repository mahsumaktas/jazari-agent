"""Tests for Ebbinghaus forgetting module."""

from datetime import datetime, timezone, timedelta
from memory.forgetting import effective_importance, should_forget


def test_fresh_memory_no_decay():
    now = datetime.now(timezone.utc)
    result = effective_importance(importance=0.8, last_accessed=now, now=now)
    assert abs(result - 0.8) < 0.01


def test_low_importance_decays_fast():
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    result = effective_importance(importance=0.3, last_accessed=week_ago, now=now)
    assert result < 0.2
    assert result > 0.05


def test_high_importance_decays_slow():
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    result = effective_importance(importance=0.95, last_accessed=week_ago, now=now)
    assert result > 0.65


def test_should_forget_threshold():
    now = datetime.now(timezone.utc)
    month_ago = now - timedelta(days=30)
    assert should_forget(importance=0.3, last_accessed=month_ago, now=now)
    assert not should_forget(importance=0.95, last_accessed=month_ago, now=now)


def test_zero_age_returns_original():
    now = datetime.now(timezone.utc)
    result = effective_importance(importance=0.5, last_accessed=now, now=now)
    assert result == 0.5
