"""Reading the Markdown dialect the curriculum and syllabus documents use.

A port of the parser primitives in the reference pipeline's `lib.mjs`. The
documents are hand-authored against a fixed section order — the vendor workbook
has fixed cell anchors, so the order is load-bearing rather than stylistic — and
these functions pull tables and sections out of that shape without a Markdown
library.

`assessment/core/markdown.py` is a Markdown *renderer* aimed at PDF output and
shares no useful surface with this.
"""

from __future__ import annotations

import re

_SEPARATOR_CELL = re.compile(r"^:?-+:?$")


def strip_md(value: object) -> str:
    """Cell text with the inline emphasis the authors use removed.

    `**TOTAL**` and `` `HN_FR_JSKS_DBF` `` have to compare equal to their plain
    forms, because the same value is written bold in a total row and plain in a
    data row.
    """
    text = str(value if value is not None else "").strip()
    text = text.replace("**", "")
    text = re.sub(r"^`|`$", "", text)
    return text.strip()


def section(text: str, start_heading: str, end_heading: str | None = None) -> str:
    """The body between two literal headings.

    Literal rather than structural on purpose: the headings are fixed by the
    export contract (`### 8. Time Allocation`), so a heading that does not match
    exactly is a document that will not export, and returning "" makes the
    verifier say so.
    """
    start = text.find(start_heading)
    if start < 0:
        return ""
    body_start = start + len(start_heading)
    end = text.find(end_heading, body_start) if end_heading else -1
    return text[body_start:].strip() if end < 0 else text[body_start:end].strip()


def md_table_rows(text: str) -> list[list[str]]:
    """Every pipe-table row in `text`, as stripped cells, separators dropped."""
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [strip_md(cell) for cell in stripped[1:-1].split("|")]
        if cells and all(_SEPARATOR_CELL.match(cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def rows_after_header(section_text: str, expected_header: list[str]) -> list[list[str]]:
    """Table rows following the header whose leading cells match `expected_header`.

    Matching on a prefix rather than the whole row lets a table carry an extra
    trailing column without breaking the reader.
    """
    rows = md_table_rows(section_text)
    for index, row in enumerate(rows):
        if all(
            cell_index < len(row) and row[cell_index] == value
            for cell_index, value in enumerate(expected_header)
        ):
            return rows[index + 1 :]
    return []


__all__ = ["md_table_rows", "rows_after_header", "section", "strip_md"]
