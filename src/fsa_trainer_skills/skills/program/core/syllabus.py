"""The topic syllabus document: `<TOPIC>_Syllabus.md`.

The section order is fixed by the export contract — the vendor workbook writes
each section to a hard-coded cell range — so this reads by literal heading and
returns "" for anything missing, letting the verifier name the absent section
rather than guessing at a shape.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fsa_trainer_skills.errors import UsageError

from .mdtable import rows_after_header, section
from .schedule import DELIVERY_TYPES

H1 = re.compile(r"^# ([A-Za-z0-9_]+) — (.+)$", re.MULTILINE)
DAYS = re.compile(r"^\*\*Days:\*\* (\d+)$", re.MULTILINE)

#: Literal section headings, in the order the export contract fixes them.
FIELDS_HEADING = "## Syllabus"
OBJECTIVES_HEADING = "### 6. Course Objectives"
OUTLINE_HEADING = "### 7. Topic Outline"
TIME_HEADING = "### 8. Time Allocation"
MATERIALS_HEADING = "### 9. Training Materials & Environments"
ASSESSMENT_HEADING = "### 10. Assessment Scheme"
DELIVERY_HEADING = "### 11. Training Delivery Principles"
AUTHOR_HEADING = "## Author and Rec of Changes"
AUTHORSHIP_HEADING = "### AUTHORSHIP"
CHANGES_HEADING = "### RECORD OF CHANGES"

OUTCOMES_LEAD = "After completing the topic, trainees will be able to:"

#: Sections the export contract has no cell for. Present in a source document,
#: they are silently dropped on export, so they are an error rather than extra.
FORBIDDEN_SECTIONS = ("### Duration", "### Prerequisites")
FORBIDDEN_FOOTER = re.compile(r"Schedule detail:", re.IGNORECASE)

PASS_CRITERIA = "Pass Criteria"


@dataclass(frozen=True)
class Objective:
    name: str
    code: str
    description: str


@dataclass(frozen=True)
class TimeRow:
    delivery_type: str
    share: float


@dataclass(frozen=True)
class AssessmentItem:
    item: str
    count: int | None
    #: None when the cell is blank, which is what Pass Criteria requires.
    weight: float | None
    notes: str


@dataclass(frozen=True)
class Author:
    role: str
    name: str
    account: str
    unit: str
    notes: str


@dataclass(frozen=True)
class Change:
    date: str
    changes: str
    action: str
    contents: str
    version: str


@dataclass(frozen=True)
class Syllabus:
    path: Path
    text: str
    code: str
    title: str
    fields: dict[int, str]
    objectives: tuple[Objective, ...]
    outcomes: tuple[str, ...]
    outline: tuple[str, ...]
    days: int
    time_rows: tuple[TimeRow, ...]
    materials: dict[str, str]
    assessments: tuple[AssessmentItem, ...]
    delivery: dict[str, str]
    authors: tuple[Author, ...]
    changes: tuple[Change, ...]

    #: Prose between the section 6 heading and the objectives table.
    objectives_lead: str = ""

    def objectives_intro(self) -> str:
        return self.objectives_lead

    def shares(self) -> dict[str, float]:
        return {row.delivery_type: row.share for row in self.time_rows}

    def author(self, role: str) -> Author | None:
        return next((a for a in self.authors if a.role == role), None)


def _number(value: str) -> float | None:
    text = value.replace("%", "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse(path: Path) -> Syllabus:
    if not path.is_file():
        raise UsageError(f"syllabus not found: {path}")
    text = path.read_text(encoding="utf-8")

    heading = H1.search(text)
    fields_text = section(text, FIELDS_HEADING, OBJECTIVES_HEADING)
    fields = {
        int(row[0]): row[2]
        for row in rows_after_header(fields_text, ["#", "Field", "Value"])
        if len(row) >= 3 and row[0].isdigit()
    }

    objectives_text = section(text, OBJECTIVES_HEADING, OUTLINE_HEADING)
    objectives_lead = objectives_text.split("| Name |")[0].strip()
    objectives = tuple(
        Objective(name=row[0], code=row[1], description=row[2])
        for row in rows_after_header(objectives_text, ["Name", "Code", "Description"])
        if len(row) >= 3 and row[0]
    )
    outcomes: tuple[str, ...] = ()
    if OUTCOMES_LEAD in objectives_text:
        tail = objectives_text[objectives_text.index(OUTCOMES_LEAD) :]
        outcomes = tuple(line[2:].strip() for line in tail.splitlines() if line.startswith("- "))

    outline_text = section(text, OUTLINE_HEADING, TIME_HEADING)
    outline = tuple(
        match.group(1).strip()
        for match in (re.match(r"^\d+\.\s+(.+)$", line) for line in outline_text.splitlines())
        if match
    )

    time_text = section(text, TIME_HEADING, MATERIALS_HEADING)
    days_match = DAYS.search(time_text)
    time_rows = tuple(
        TimeRow(delivery_type=row[0], share=_number(row[1]) or 0.0)
        for row in rows_after_header(time_text, ["Delivery Type", "Share"])
        if len(row) >= 2 and row[0] in DELIVERY_TYPES
    )

    materials_text = section(text, MATERIALS_HEADING, ASSESSMENT_HEADING)
    materials = {
        row[0]: row[1]
        for row in rows_after_header(materials_text, ["Item", "Value"])
        if len(row) >= 2 and row[0]
    }

    assessment_text = section(text, ASSESSMENT_HEADING, DELIVERY_HEADING)
    assessments = tuple(
        AssessmentItem(
            item=row[0],
            count=int(_number(row[1])) if _number(row[1]) is not None else None,
            weight=_number(row[2]),
            notes=row[3] if len(row) > 3 else "",
        )
        for row in rows_after_header(assessment_text, ["Item", "Count", "Weight", "Notes"])
        if len(row) >= 3 and row[0]
    )

    delivery_text = section(text, DELIVERY_HEADING, AUTHOR_HEADING)
    delivery = {
        row[0]: row[1]
        for row in rows_after_header(delivery_text, ["Item", "Value"])
        if len(row) >= 2 and row[0]
    }

    author_text = section(text, AUTHORSHIP_HEADING, CHANGES_HEADING)
    authors = tuple(
        Author(role=row[0], name=row[1], account=row[2], unit=row[3], notes=row[4])
        for row in rows_after_header(author_text, ["Role", "Name", "Account", "Unit", "Notes"])
        if len(row) >= 5 and row[0]
    )

    changes_text = section(text, CHANGES_HEADING, None)
    changes = tuple(
        Change(date=row[0], changes=row[1], action=row[2], contents=row[3], version=row[4])
        # "A*, M, D" carries a literal asterisk, and the preamble line above the
        # table is `\*A - Added ...` — neither is a table row, and neither may
        # be mistaken for one.
        for row in rows_after_header(changes_text, ["Date", "Changes", "A*, M, D"])
        if len(row) >= 5 and row[0]
    )

    return Syllabus(
        path=path,
        text=text,
        code=heading.group(1) if heading else "",
        title=heading.group(2).strip() if heading else "",
        fields=fields,
        objectives=objectives,
        objectives_lead=objectives_lead,
        outcomes=outcomes,
        outline=outline,
        days=int(days_match.group(1)) if days_match else 0,
        time_rows=time_rows,
        materials=materials,
        assessments=assessments,
        delivery=delivery,
        authors=authors,
        changes=changes,
    )


__all__ = [
    "FORBIDDEN_FOOTER",
    "FORBIDDEN_SECTIONS",
    "PASS_CRITERIA",
    "AssessmentItem",
    "Author",
    "Change",
    "Objective",
    "Syllabus",
    "TimeRow",
    "parse",
]
