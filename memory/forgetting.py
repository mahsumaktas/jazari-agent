"""Ebbinghaus forgetting curve — lazy decay computation on search."""

from datetime import datetime, timezone
from math import exp

FORGET_THRESHOLD = 0.1
STABILITY_MULTIPLIER = 30


def effective_importance(
    importance: float,
    last_accessed: datetime,
    now: datetime | None = None,
) -> float:
    if now is None:
        now = datetime.now(timezone.utc)

    age_days = max((now - last_accessed).total_seconds() / 86400, 0)
    if age_days == 0:
        return importance

    stability = max(importance * STABILITY_MULTIPLIER, 1)
    retention = exp(-age_days / stability)
    return importance * retention


def should_forget(
    importance: float,
    last_accessed: datetime,
    now: datetime | None = None,
    threshold: float = FORGET_THRESHOLD,
) -> bool:
    return effective_importance(importance, last_accessed, now) < threshold
