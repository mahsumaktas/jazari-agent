"""Guardrails — safety callbacks for Jazari agents (ADK best practice)."""

from google.genai import types

BLOCKED_TOPICS = [
    "suicide", "self-harm", "harm others",
    "illegal drugs", "weapons",
]

SAFETY_RESPONSE = (
    "I'm a life coach, not a crisis counselor. "
    "If you're in crisis, please contact a professional: "
    "call 182 (Turkey) or text HOME to 741741 (US Crisis Text Line)."
)


async def safety_guardrail(callback_context, **kwargs) -> types.Content | None:
    """Check user messages for crisis/safety topics before model processes them.

    Returns None to proceed normally, or a Content object to short-circuit.
    """
    # Try both public and private attribute names for ADK compatibility
    invocation = getattr(callback_context, 'invocation_context', None) or \
                 getattr(callback_context, '_invocation_context', None)

    if not invocation:
        return None

    user_content = getattr(invocation, 'user_content', None)
    if not user_content or not user_content.parts:
        return None

    user_text = ""
    for part in user_content.parts:
        if hasattr(part, "text") and part.text:
            user_text += part.text.lower()

    if not user_text:
        return None

    for topic in BLOCKED_TOPICS:
        if topic in user_text:
            return types.Content(
                role="model",
                parts=[types.Part.from_text(text=SAFETY_RESPONSE)],
            )

    return None
