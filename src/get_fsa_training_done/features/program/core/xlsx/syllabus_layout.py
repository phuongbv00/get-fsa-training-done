"""Where each part of a syllabus goes in the vendor form.

Every reference here was read off the real template, and `probe.py` re-checks
the load-bearing ones before a write: addressing row 28 because that is where
the assessment block starts is only safe if something first confirms it still
is. Handed a revised form, a writer does not fail — it writes the right value
into the wrong cell.

Two things are deliberately *not* written as literals:

* The Time Allocation percentages stay formulas pointing at the schedule
  sheet's summary block, so the workbook recomputes them from the rows we
  populate. The template maps those by **label**, not position — its summary
  block lists the delivery types in a different order from the syllabus table —
  so this resolves them by label too, which also repairs the two cells the
  vendor left as a literal `0`.
* Nothing touches `styles.xml`. This populates a formatted template and copies
  the style a cell already has; it cannot invent one.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schedule import SCHEDULE_HEADER
from ..syllabus import Syllabus
from . import refs
from .package import XlsxPackage
from .probe import Expect
from .sheetxml import Sheet

SYLLABUS_SHEET = "<Topic Code>_Syllabus"
SCHEDULE_SHEET = "<Topics Code>_ScheduleDetail"
AUTHOR_SHEET = "Author and Rec of Changes"
IDENTITY_SHEET = "DV-IDENTITY-0"

#: Fields 1-5 of the syllabus table.
FIELD_ROWS = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6}
OBJECTIVES_INTRO = "C7"
OBJECTIVE_ROWS = range(9, 16)
OUTCOMES = "C16"
OUTLINE = "C17"
TIME_ROWS = range(18, 25)
SESSIONS_CELL = "F18"
MATERIAL_ROWS = {"Text book": 25, "References": 26, "Technical requirements": 27}
ASSESSMENT_ROWS = range(28, 33)
DELIVERY_ROWS = range(33, 40)

#: The session plan's band, and the summary block below it.
FIRST_DATA_ROW = 3
LAST_DATA_ROW = 68
SUMMARY_ROWS = range(70, 77)
SUMMARY_LABEL_COLUMN = "F"
SUMMARY_SHARE_COLUMN = "H"

AUTHOR_ROWS = {"Creator": 3, "Reviewer": 4, "Approver": 5}
CHANGE_FIRST_ROW = 10
CHANGE_LAST_ROW = 14

MAX_DATA_ROWS = LAST_DATA_ROW - FIRST_DATA_ROW + 1

EXPECTATIONS = [
    Expect(SYLLABUS_SHEET, "A2", "1"),
    Expect(SYLLABUS_SHEET, "A7", "6"),
    Expect(SYLLABUS_SHEET, "A18", "8"),
    Expect(SYLLABUS_SHEET, "A28", "10"),
    Expect(SYLLABUS_SHEET, "A33", "11"),
]
REQUIRED_SHEETS = [SYLLABUS_SHEET, SCHEDULE_SHEET, AUTHOR_SHEET]


@dataclass(frozen=True)
class Geometry:
    """Everything addressed by a fixed reference, in one place."""

    syllabus_sheet: str = SYLLABUS_SHEET
    schedule_sheet: str = SCHEDULE_SHEET
    author_sheet: str = AUTHOR_SHEET
    first_data_row: int = FIRST_DATA_ROW
    last_data_row: int = LAST_DATA_ROW


def shared_string(package: XlsxPackage, sheet: Sheet, ref: str) -> str:
    """A template label, whether it is inline or a shared-string index."""
    element = sheet.cell(ref, create=False)
    if element is None:
        return ""
    if element.get("t") == "s":
        index = sheet.value_of(ref)
        return package.shared_strings()[int(index)] if index and index.isdigit() else ""
    return sheet.value_of(ref) or ""


def summary_rows_by_label(package: XlsxPackage, schedule: Sheet) -> dict[str, int]:
    """Delivery type -> the summary row that totals it."""
    found = {}
    for row in SUMMARY_ROWS:
        label = shared_string(package, schedule, f"{SUMMARY_LABEL_COLUMN}{row}")
        if label:
            found[label.strip()] = row
    return found


def write_schedule(sheet: Sheet, rows: list[dict[str, str]]) -> None:
    """Fill the session-plan band and re-merge it around the new grouping.

    The template's band ships full of sample merges (`A3:A9`, `C5:C9`). Left in
    place they swallow the rows written under them, so the merges are rebuilt
    from the data — every other merge on the sheet is preserved.
    """
    columns = [refs.column_letter(index) for index in range(1, len(SCHEDULE_HEADER) + 1)]
    for row in range(FIRST_DATA_ROW, LAST_DATA_ROW + 1):
        for column in columns:
            sheet.clear(f"{column}{row}")

    numeric = {"Session", "Duration (mins)"}
    for offset, record in enumerate(rows):
        target = FIRST_DATA_ROW + offset
        for column, header in zip(columns, SCHEDULE_HEADER):
            value = record.get(header, "")
            ref = f"{column}{target}"
            if header in numeric:
                try:
                    sheet.set_number(ref, float(value))
                    continue
                except (TypeError, ValueError):
                    pass
            if value:
                sheet.set_text(ref, value)

    keep = [
        merge
        for merge in sheet.merges()
        if not (
            FIRST_DATA_ROW <= refs.split(merge.split(":")[0])[1] <= LAST_DATA_ROW
            or FIRST_DATA_ROW <= refs.split(merge.split(":")[1])[1] <= LAST_DATA_ROW
        )
    ]
    sheet.set_merges(keep + _band_merges(rows))


def _band_merges(rows: list[dict[str, str]]) -> list[str]:
    """Merge the Unit, Chapter and Session columns over contiguous runs."""
    merges: list[str] = []
    for columns, key in ((("A", "B"), ("Unit", "Training Unit/Chapter")), (("C",), ("Session",))):
        start = 0
        while start < len(rows):
            end = start
            while end + 1 < len(rows) and all(
                rows[end + 1].get(name, "") == rows[start].get(name, "") for name in key
            ):
                end += 1
            if end > start:
                for column in columns:
                    merges.append(
                        f"{column}{FIRST_DATA_ROW + start}:{column}{FIRST_DATA_ROW + end}"
                    )
            start = end + 1
    return merges


def write_syllabus(
    package: XlsxPackage,
    sheet: Sheet,
    schedule: Sheet,
    syllabus: Syllabus,
    *,
    schedule_sheet_name: str,
    session_count: int,
) -> None:
    for number, row in FIELD_ROWS.items():
        sheet.set_text(f"C{row}", syllabus.fields.get(number, ""))

    sheet.set_text(OBJECTIVES_INTRO, syllabus.objectives_intro())
    for offset, row in enumerate(OBJECTIVE_ROWS):
        if offset < len(syllabus.objectives):
            objective = syllabus.objectives[offset]
            sheet.set_text(f"C{row}", objective.name)
            sheet.set_text(f"D{row}", objective.code)
            sheet.set_text(f"E{row}", objective.description)
        else:
            for column in "CDE":
                sheet.clear(f"{column}{row}")

    sheet.set_text(OUTCOMES, "\n".join(f"- {line}" for line in syllabus.outcomes))
    sheet.set_text(
        OUTLINE, "\n".join(f"{n}. {item}" for n, item in enumerate(syllabus.outline, start=1))
    )

    by_label = summary_rows_by_label(package, schedule)
    for row in TIME_ROWS:
        label = shared_string(package, sheet, f"C{row}").strip()
        summary_row = by_label.get(label)
        if summary_row is None:
            continue
        sheet.set_formula(
            f"D{row}",
            f"'{schedule_sheet_name}'!{SUMMARY_SHARE_COLUMN}{summary_row}",
        )
    sheet.set_text(SESSIONS_CELL, f"{session_count} Sessions")

    for label, row in MATERIAL_ROWS.items():
        sheet.set_text(f"D{row}", syllabus.materials.get(label, ""))

    for offset, row in enumerate(ASSESSMENT_ROWS):
        if offset < len(syllabus.assessments):
            item = syllabus.assessments[offset]
            sheet.set_text(f"C{row}", item.item)
            if item.count is not None:
                sheet.set_number(f"D{row}", item.count)
            else:
                sheet.clear(f"D{row}")
            if item.weight is not None:
                sheet.set_number(f"E{row}", item.weight)
            else:
                sheet.clear(f"E{row}")
            sheet.set_text(f"F{row}", item.notes)
        else:
            for column in "CDEF":
                sheet.clear(f"{column}{row}")

    for row in DELIVERY_ROWS:
        label = shared_string(package, sheet, f"C{row}").strip()
        if label in syllabus.delivery:
            sheet.set_text(f"D{row}", syllabus.delivery[label])


def write_authors(package: XlsxPackage, sheet: Sheet, syllabus: Syllabus) -> None:
    for role, row in AUTHOR_ROWS.items():
        author = syllabus.author(role)
        for column, value in zip(
            "CDEF",
            (
                author.name if author else "",
                author.account if author else "",
                author.unit if author else "",
                author.notes if author else "",
            ),
        ):
            sheet.set_text(f"{column}{row}", value)

    for offset, row in enumerate(range(CHANGE_FIRST_ROW, CHANGE_LAST_ROW + 1)):
        if offset < len(syllabus.changes):
            change = syllabus.changes[offset]
            for column, value in zip(
                "BCDEF",
                (change.date, change.changes, change.action, change.contents, change.version),
            ):
                sheet.set_text(f"{column}{row}", value)
        else:
            for column in "BCDEF":
                sheet.clear(f"{column}{row}")


__all__ = [
    "AUTHOR_SHEET",
    "EXPECTATIONS",
    "IDENTITY_SHEET",
    "MAX_DATA_ROWS",
    "REQUIRED_SHEETS",
    "SCHEDULE_SHEET",
    "SYLLABUS_SHEET",
    "Geometry",
    "summary_rows_by_label",
    "write_authors",
    "write_schedule",
    "write_syllabus",
]
