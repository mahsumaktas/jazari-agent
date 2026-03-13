"""Tests for safety guardrail callbacks."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from agents.guardrails import safety_guardrail, SAFETY_RESPONSE, BLOCKED_TOPICS


def _make_callback_context(user_text: str):
    """Create a mock CallbackContext with user text."""
    ctx = MagicMock()
    part = MagicMock()
    part.text = user_text
    ctx.invocation_context.user_content.parts = [part]
    return ctx


def _make_empty_context():
    """Create a mock CallbackContext with no user content."""
    ctx = MagicMock()
    ctx.invocation_context.user_content = None
    return ctx


async def test_normal_message_passes():
    """Normal messages should not be blocked."""
    ctx = _make_callback_context("I want to improve my fitness routine")
    result = await safety_guardrail(ctx)
    assert result is None


async def test_crisis_topic_blocked():
    """Crisis topics should return safety response."""
    ctx = _make_callback_context("I've been thinking about self-harm lately")
    result = await safety_guardrail(ctx)
    assert result is not None
    assert result.parts[0].text == SAFETY_RESPONSE


async def test_empty_message_passes():
    """Empty user content should pass through."""
    ctx = _make_empty_context()
    result = await safety_guardrail(ctx)
    assert result is None


async def test_case_insensitive():
    """Detection should be case-insensitive."""
    ctx = _make_callback_context("SELF-HARM is a serious topic")
    result = await safety_guardrail(ctx)
    assert result is not None


async def test_all_blocked_topics():
    """All blocked topics should trigger the guardrail."""
    for topic in BLOCKED_TOPICS:
        ctx = _make_callback_context(f"I want to talk about {topic}")
        result = await safety_guardrail(ctx)
        assert result is not None, f"Topic '{topic}' was not blocked"
