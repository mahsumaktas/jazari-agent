"""Tests for importance scoring module."""

import pytest
from unittest.mock import patch, AsyncMock
from memory.scoring import score_importance, SCORING_PROMPT_TEMPLATE


def test_prompt_template_has_placeholders():
    prompt = SCORING_PROMPT_TEMPLATE.format(content="test", memory_type="fact")
    assert "test" in prompt
    assert "fact" in prompt


@pytest.mark.asyncio
async def test_score_returns_float_in_range():
    mock_response = AsyncMock()
    mock_response.text = "0.75"
    with patch("memory.scoring._generate_async", return_value=mock_response):
        score = await score_importance("User's name is Mehmet", "fact")
        assert 0.0 <= score <= 1.0
        assert score == 0.75


@pytest.mark.asyncio
async def test_score_handles_malformed_response():
    mock_response = AsyncMock()
    mock_response.text = "this is not a number"
    with patch("memory.scoring._generate_async", return_value=mock_response):
        score = await score_importance("random text", "event")
        assert score == 0.5


@pytest.mark.asyncio
async def test_score_clamps_out_of_range():
    mock_response = AsyncMock()
    mock_response.text = "1.5"
    with patch("memory.scoring._generate_async", return_value=mock_response):
        score = await score_importance("test", "fact")
        assert score == 1.0
