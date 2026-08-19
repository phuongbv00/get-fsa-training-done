"""How long a brief is allowed to be.

A learner brief has to be readable inside the time it is given, so length is
derived from the stated duration rather than left to judgement: two A4 pages per
hour, floor of two pages. `render` enforces it after rendering and `verify`
re-checks it, which is why the parsing lives here rather than in either.

The original scripts each carried their own copy of `parse_duration_hours` and
they had drifted — only one of them recognised the Vietnamese units that appear
in `_vn` briefs, so the same file could pass one check and fail the other. This
is the merged version.
"""

from __future__ import annotations

import re

#: House rule: two A4 pages per hour of stated duration.
PAGES_PER_HOUR = 2
#: Even a very short assessment gets a title page plus one page of tasks.
MIN_PAGE_BUDGET = 2

_DURATION_LINE = re.compile(r"^>\s*\*\*Duration:\*\*\s*(.+)$", re.MULTILINE)
_HOURS = re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h\b|gi[oờ])")
_MINUTES = re.compile(r"(\d+)\s*(?:minutes?|mins?|ph[uú]t)")
_DAYS = re.compile(r"(\d+(?:\.\d+)?)\s*(?:days?|ng[aà]y)")
_WEEKS = re.compile(r"(\d+(?:\.\d+)?)\s*(?:weeks?|tu[aầ]n)")


def duration_text(markdown: str) -> str | None:
    """The raw value of the brief's `> **Duration:**` banner line."""
    match = _DURATION_LINE.search(markdown)
    return match.group(1).strip() if match else None


def parse_duration_hours(markdown: str) -> float | None:
    """Duration in hours, or None when it is not expressed in clock time.

    Multi-day durations return None deliberately: a three-day assignment is not
    a six-page brief, and the page budget only means something for work done in
    one sitting. `days_or_weeks` reports those separately.
    """
    text = duration_text(markdown)
    if text is None:
        return None
    lowered = text.lower()
    if _DAYS.search(lowered) or _WEEKS.search(lowered):
        return None
    hours = _HOURS.search(lowered)
    if hours:
        return float(hours.group(1))
    minutes = _MINUTES.search(lowered)
    if minutes:
        return int(minutes.group(1)) / 60
    return None


def parse_duration_days(markdown: str) -> float | None:
    """Duration in days, for the assignment types measured that way."""
    text = duration_text(markdown)
    if text is None:
        return None
    lowered = text.lower()
    weeks = _WEEKS.search(lowered)
    if weeks:
        return float(weeks.group(1)) * 7
    days = _DAYS.search(lowered)
    if days:
        return float(days.group(1))
    return None


def page_budget_for(markdown: str, *, override: int | None = None) -> tuple[int | None, str]:
    """Return `(budget, source)`; budget is None when none applies.

    `source` names where the number came from, so the caller can say so in its
    output — "4/4 pages (budget from Duration header)" is a measurement, while
    "looks about right" is not.
    """
    if override is not None:
        return override, "--max-pages"

    hours = parse_duration_hours(markdown)
    if hours is not None:
        return max(MIN_PAGE_BUDGET, int(hours * PAGES_PER_HOUR)), "Duration header"

    days = parse_duration_days(markdown)
    if days is not None:
        # Multi-day work is scoped by task count, not by how long the learner
        # sits with the brief, so there is no page budget to enforce.
        return None, "multi-day duration (no page budget)"

    return None, "no Duration header"
