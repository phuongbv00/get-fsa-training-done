"""Programme and topic codes.

A code reads `SITE_LEVEL_TRACK_SUBJECT` — `HN_FR_JSKS_JAVA_WEB` is Hanoi,
Fresher, the JS/KS track, Java web. A topic code is the programme code with its
last segment replaced: `HN_FR_JSKS_DBF`.

The second segment is a **level**, from the same vocabulary
`fsa-training-assessment` calibrates against. That shared table is the reason
`levels.py` sits beside `errors.py` rather than inside one skill: a programme
declares the audience its codes claim, and an assessment calibrates for it, and
the two must spell it the same way. The abbreviations below are this skill's
own — a code segment is a filename convention, not part of the level table.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from fsa_trainer_skills import levels

#: Code segment -> level key. `CPL` and `FR` are written out in full; the
#: banded levels are abbreviated because a code segment is short by convention.
SEGMENT_TO_LEVEL = {
    "CPL": "CPL",
    "FR": "FR",
    "US": "UP_SKILL",
    "RS": "RE_SKILL",
}

SEGMENT = re.compile(r"^[A-Z0-9]+$")


@dataclass(frozen=True)
class Code:
    raw: str
    site: str
    level_segment: str
    track: str
    subject: str

    @property
    def prefix(self) -> str:
        """The part every topic in a programme shares."""
        return f"{self.site}_{self.level_segment}_{self.track}"

    def sibling(self, subject: str) -> str:
        return f"{self.prefix}_{subject}"


class CodeError(ValueError):
    pass


def parse(code: str) -> Code:
    parts = code.strip().split("_")
    if len(parts) < 4:
        raise CodeError(
            f"{code!r} does not read SITE_LEVEL_TRACK_SUBJECT (needs at least four segments)"
        )
    site, level_segment, track, *subject = parts
    for part in (site, level_segment, track):
        if not SEGMENT.match(part):
            raise CodeError(f"{code!r}: segment {part!r} must be upper-case alphanumeric")
    return Code(
        raw=code.strip(),
        site=site,
        level_segment=level_segment,
        track=track,
        # A subject may itself contain underscores: JAVA_WEB is one subject.
        subject="_".join(subject),
    )


def level_key_for(code: str) -> str | None:
    """The level key a code claims, or None when its segment names no known one.

    None rather than an error: a site may use a segment this table has never
    seen, and that is a warning about a convention, not a broken document.
    """
    try:
        parsed = parse(code)
    except CodeError:
        return None
    return SEGMENT_TO_LEVEL.get(parsed.level_segment)


def level_for(code: str) -> levels.Level | None:
    """The single level a code pins down, if it pins one down at all.

    `UP_SKILL` and `RE_SKILL` split into junior/mid/senior with *different*
    audiences, and a code carries no band — so those return None rather than
    quietly standing in the junior band and inviting a check against an audience
    the programme never claimed. Only `CPL` and `FR` are unambiguous from a code.
    """
    key = level_key_for(code)
    if key is None:
        return None
    try:
        return levels.resolve(key)
    except levels.UnknownLevel:
        return None


__all__ = ["SEGMENT_TO_LEVEL", "Code", "CodeError", "level_for", "level_key_for", "parse"]
