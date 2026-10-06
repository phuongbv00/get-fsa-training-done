"""Rule bodies, grouped by what they read.

Each finding names the rule that produced it, and every id declared in
`core/rules.py` must appear in exactly one of these modules — a test asserts
both directions, so a rule cannot be documented without being enforced or
enforced without being documented.
"""

from __future__ import annotations

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def weekday_index(name: str) -> int:
    try:
        return WEEKDAYS.index(name.strip().lower()[:3])
    except ValueError:
        from get_fsa_training_done.errors import UsageError

        raise UsageError(f"unknown weekday {name!r}; choose from {', '.join(WEEKDAYS)}") from None


def as_number(value: str) -> float | None:
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


__all__ = ["WEEKDAYS", "as_number", "weekday_index"]
