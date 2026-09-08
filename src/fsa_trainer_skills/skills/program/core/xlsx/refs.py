"""Cell references: `A1`, `AA10`, `A1:I68`."""

from __future__ import annotations

import re

CELL = re.compile(r"^([A-Z]+)(\d+)$")
RANGE = re.compile(r"^([A-Z]+\d+):([A-Z]+\d+)$")


def column_index(letters: str) -> int:
    """`A` -> 1, `Z` -> 26, `AA` -> 27."""
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index


def column_letter(index: int) -> str:
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def split(ref: str) -> tuple[int, int]:
    """`B7` -> (column 2, row 7)."""
    match = CELL.match(ref.upper().replace("$", ""))
    if not match:
        raise ValueError(f"not a cell reference: {ref!r}")
    return column_index(match.group(1)), int(match.group(2))


def cell(column: int, row: int) -> str:
    return f"{column_letter(column)}{row}"


def expand(range_ref: str) -> list[str]:
    """Every cell in `A1:B2`, row by row."""
    match = RANGE.match(range_ref.upper().replace("$", ""))
    if not match:
        raise ValueError(f"not a range: {range_ref!r}")
    (c1, r1), (c2, r2) = split(match.group(1)), split(match.group(2))
    return [
        cell(column, row)
        for row in range(min(r1, r2), max(r1, r2) + 1)
        for column in range(min(c1, c2), max(c1, c2) + 1)
    ]


def bounds(refs: list[str]) -> str:
    """The smallest range covering `refs` — a sheet's `dimension`."""
    if not refs:
        return "A1"
    coords = [split(ref) for ref in refs]
    columns = [c for c, _ in coords]
    rows = [r for _, r in coords]
    return f"{cell(min(columns), min(rows))}:{cell(max(columns), max(rows))}"


__all__ = ["bounds", "cell", "column_index", "column_letter", "expand", "split"]
