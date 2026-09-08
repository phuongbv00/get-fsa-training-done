"""Matching an Assessment Scheme item to the sessions that deliver it.

The reference pipeline special-cased two topic codes: one because it ran three
short assignments instead of one long one, another because a capstone is graded
by sprint reviews. Neither is a property of the *code* — they are properties of
the scheme the syllabus already declares — so this matches on item name and
lets both fall out.

The subtlety is what counts as one assessment. A long assignment occupies three
sessions (kickoff, completion, acceptance) and is one assignment; a final review
runs in two parts and is one review; but Quiz 1 and Quiz 2 are two quizzes. So
an occurrence is the item plus its **ordinal**, and rows that carry no ordinal —
lifecycle stages, parts — collapse into a single occurrence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .schedule import DELIVERY_TYPES

#: Stripped before looking for an ordinal, so "Part A" and a hypothetical
#: "Part 2" both stay parts of one assessment rather than becoming two.
PART_QUALIFIER = re.compile(r"[—–-]?\s*\bpart\s+\w+", re.IGNORECASE)


@dataclass(frozen=True)
class ItemContract:
    item: str
    #: Matched against the row's Content, anchored at the start.
    content: re.Pattern | None = None
    #: Required delivery type, when the type is the defining signal.
    delivery_type: str | None = None
    #: Captures the occurrence number, when the content carries one.
    ordinal: re.Pattern | None = None

    def matches(self, content: str, delivery_type: str) -> bool:
        if self.delivery_type is not None and delivery_type != self.delivery_type:
            return False
        if self.content is not None and not self.content.search(content):
            return False
        return self.content is not None or self.delivery_type is not None

    def key(self, content: str) -> str:
        """What makes this row a distinct occurrence of the item."""
        if self.ordinal is None:
            return self.item
        match = self.ordinal.search(PART_QUALIFIER.sub("", content))
        return f"{self.item} {match.group(1)}" if match else self.item


DEFAULTS: tuple[ItemContract, ...] = (
    ItemContract(
        item="Quiz",
        delivery_type="Test/Quiz",
        ordinal=re.compile(r"\bquiz\s+(\d+)", re.IGNORECASE),
    ),
    ItemContract(
        item="Assignment",
        content=re.compile(r"^\s*(?:short|long)\s+assignment\b", re.IGNORECASE),
        ordinal=re.compile(r"\bassignment\s+(\d+)", re.IGNORECASE),
    ),
    ItemContract(
        item="Final Theory Exam",
        content=re.compile(r"^\s*final\s+theory\s+exam\b", re.IGNORECASE),
    ),
    ItemContract(
        item="Final Practice Exam",
        content=re.compile(r"^\s*final\s+practice\s+exam\b", re.IGNORECASE),
    ),
    ItemContract(
        item="Sprint Review",
        content=re.compile(r"^\s*sprint\s+review\b", re.IGNORECASE),
        ordinal=re.compile(r"\bsprint\s+review\s+(\d+)", re.IGNORECASE),
    ),
    ItemContract(
        item="Final Review",
        content=re.compile(r"^\s*final\s+review\b", re.IGNORECASE),
    ),
)


def registry(overrides: dict[str, str] | None = None) -> dict[str, ItemContract]:
    """The default contracts, with any `--item-pattern` overrides applied."""
    table = {contract.item: contract for contract in DEFAULTS}
    for item, pattern in (overrides or {}).items():
        existing = table.get(item)
        table[item] = ItemContract(
            item=item,
            content=re.compile(pattern, re.IGNORECASE),
            ordinal=existing.ordinal if existing else None,
        )
    return table


def count_occurrences(contract: ItemContract, rows: list[dict[str, str]]) -> int:
    """How many distinct occurrences of `contract` the session plan delivers."""
    keys = {
        contract.key(row.get("Content", ""))
        for row in rows
        if contract.matches(row.get("Content", ""), row.get("Delivery Type", ""))
    }
    return len(keys)


def parse_overrides(values: list[str] | None) -> dict[str, str]:
    """`--item-pattern "Name=REGEX"`, repeatable."""
    overrides: dict[str, str] = {}
    for raw in values or []:
        item, separator, pattern = raw.partition("=")
        if not separator or not item.strip() or not pattern.strip():
            from fsa_trainer_skills.errors import UsageError

            raise UsageError(f"--item-pattern expects 'Item=REGEX', got {raw!r}")
        overrides[item.strip()] = pattern.strip()
    return overrides


__all__ = [
    "DEFAULTS",
    "DELIVERY_TYPES",
    "ItemContract",
    "count_occurrences",
    "parse_overrides",
    "registry",
]
