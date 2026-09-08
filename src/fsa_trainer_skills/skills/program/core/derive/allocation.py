"""Section 8, Time Allocation, from the session plan it summarises.

Each share is `round(type_minutes / total_minutes * 100, 2)` over the fixed
delivery-type order. `verify` checks the same arithmetic, so a syllabus this
writes passes PRG-S09 by construction.
"""

from __future__ import annotations

import re

from fsa_trainer_skills.errors import UsageError

from ..schedule import DELIVERY_TYPES
from ..syllabus import MATERIALS_HEADING, TIME_HEADING

TOTAL_ROW = "| **Total** | **100.00%** |"


def shares(rows: list[dict[str, str]]) -> dict[str, float]:
    total = 0.0
    by_type: dict[str, float] = {name: 0.0 for name in DELIVERY_TYPES}
    for row in rows:
        raw = row.get("Duration (mins)", "").strip()
        try:
            minutes = float(raw)
        except ValueError:
            raise UsageError(f"duration {raw!r} is not a number") from None
        total += minutes
        delivery = row.get("Delivery Type", "")
        if delivery not in by_type:
            raise UsageError(f"unknown delivery type {delivery!r}")
        by_type[delivery] += minutes
    if total <= 0:
        raise UsageError("the session plan has no minutes to allocate")
    return {name: round(minutes / total * 100, 2) for name, minutes in by_type.items()}


def total_minutes(rows: list[dict[str, str]]) -> float:
    return sum(float(row.get("Duration (mins)", 0) or 0) for row in rows)


def render(rows: list[dict[str, str]], *, days: int | None) -> str:
    """The section body, exactly as it appears between headings 8 and 9."""
    lines = []
    if days is not None:
        lines += [f"**Days:** {days}", ""]
    lines += ["| Delivery Type | Share |", "|---|---:|"]
    for name, share in shares(rows).items():
        lines.append(f"| {name} | {share:.2f}% |")
    lines.append(TOTAL_ROW)
    return "\n".join(lines)


def days_for(rows: list[dict[str, str]], minutes_per_day: int) -> int:
    minutes = total_minutes(rows)
    if minutes % minutes_per_day:
        raise UsageError(
            f"{minutes:g} minutes is not a whole number of {minutes_per_day}-minute days",
            hint="fix the session plan, or pass the training day this programme uses",
        )
    return int(minutes // minutes_per_day)


def patch(text: str, body: str) -> str:
    """Replace section 8's body in a syllabus, leaving everything else alone."""
    pattern = re.compile(
        rf"({re.escape(TIME_HEADING)}\n\n).*?(\n\n{re.escape(MATERIALS_HEADING)})",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise UsageError(
            f"could not find a '{TIME_HEADING}' section followed by '{MATERIALS_HEADING}'"
        )
    return pattern.sub(lambda m: f"{m.group(1)}{body}{m.group(2)}", text, count=1)


__all__ = ["TOTAL_ROW", "days_for", "patch", "render", "shares", "total_minutes"]
