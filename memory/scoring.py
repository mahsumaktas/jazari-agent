"""Importance scoring via Gemini Flash — rates memories 0.0-1.0."""

import asyncio
from google import genai

SCORING_PROMPT_TEMPLATE = """Rate memory importance 0.0-1.0:
- 0.9-1.0: goals, deadlines, health conditions, life events
- 0.7-0.8: habits, recurring patterns, preferences
- 0.4-0.6: daily activities, meals, casual observations
- 0.1-0.3: small talk, weather, filler

Memory: "{content}"
Type: {memory_type}
Return ONLY a float."""

DEFAULT_SCORE = 0.5

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


async def _generate_async(prompt: str):
    client = _get_client()
    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            ),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        raise TimeoutError("Gemini scoring timed out after 10s")
    return response


async def score_importance(content: str, memory_type: str) -> float:
    prompt = SCORING_PROMPT_TEMPLATE.format(content=content, memory_type=memory_type)

    try:
        response = await _generate_async(prompt)
        text = response.text.strip()
        score = float(text)
        return max(0.0, min(1.0, score))
    except (ValueError, TypeError, AttributeError):
        return DEFAULT_SCORE
    except (TimeoutError, asyncio.TimeoutError):
        return DEFAULT_SCORE
    except Exception:
        return DEFAULT_SCORE
