"""Marks as FAMS's theory mark template: one row per trainee per test, a final mark only.

Quizzes and the theory exam take this form, one sheet:

    Email or Account, Full Name, TopicCode, TestName, Final Mark (/10), Score, Total Score

The marks come from one of two sources:

- **a quiz-score CSV** (`grade quiz-score`) — a module's quizzes, one column
  each, stacked as one block of rows per quiz and named `Quiz_1`, `Quiz_2`, …
  in column order unless named otherwise. A quiz a trainee did not sit is 0.
- **a grade CSV** (`grade aggregate` or `merge-retake`) — one test, a written
  theory exam, its `Total` the mark. Its name is the assessment's code on FAMS:
  given, or the one the template's rows carry.

Who is in the class, which account a row carries and why nothing is blank are
the rules in `fams`. A template's header row is kept as it is, extra columns
and all. Final Mark and Score are the mark out of 10, Total Score is 10.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from get_fsa_training_done.errors import UsageError

from . import quiz_scores
from .fams import NS, Marks, Report, write_workbook
from .roster import Roster

ACCOUNT = "Email or Account"
NAME = "Full Name"
TOPIC = "TopicCode"
TEST = "TestName"
MARK = "Final Mark (/10)"
SCORE = "Score"
TOTAL = "Total Score"
HEADERS = [ACCOUNT, NAME, TOPIC, TEST, MARK, SCORE, TOTAL]
SHEET = "Result"


@dataclass(frozen=True)
class Entry:
    std_id: str
    name: str
    marks: tuple[str, ...]


@dataclass
class Scores:
    """A source's tests and its rows, one mark per test."""

    labels: list[str]
    entries: list[Entry]
    #: Read from a grade CSV: one test, with no default name.
    from_grades: bool = False


@dataclass
class Sheet:
    headers: list[str]
    rows: list[list[str | float]]


# --- the sources -------------------------------------------------------------------


def _rows(path: Path, what: str) -> list[list[str]]:
    if not path.is_file():
        raise UsageError(f"{what} not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.reader(handle))


def read_quiz_scores(path: Path) -> Scores:
    """A `grade quiz-score` CSV: `No, ID, Name, <one column per quiz>`."""
    rows = _rows(path, "quiz-score CSV")
    if not rows or rows[0][:3] != ["No", "ID", "Name"] or len(rows[0]) < 4:
        raise UsageError(f"{path} is not `grade quiz-score` output (No, ID, Name, <quiz>…)")
    labels = rows[0][3:]
    entries = [
        Entry(
            std_id=row[1].strip(),
            name=row[2].strip() if len(row) > 2 else "",
            marks=tuple(
                (row[3 + i] if 3 + i < len(row) else "").strip() for i in range(len(labels))
            ),
        )
        for row in rows[1:]
        if len(row) > 1 and row[1].strip()
    ]
    return Scores(labels, entries)


def read_grades(path: Path) -> Scores:
    """A `grade aggregate` (or `merge-retake`) CSV, its `Total` the one mark."""
    rows = _rows(path, "grade CSV")
    if not rows or rows[0][:2] != ["Std ID", "Name"] or rows[0][-1] != "Total":
        raise UsageError(f"{path} is not `grade aggregate` output (Std ID, Name, …, Total)")
    entries = [
        Entry(std_id=row[0].strip(), name=row[1].strip(), marks=(row[-1].strip(),))
        for row in rows[1:]
        if len(row) == len(rows[0]) and row[0].strip()
    ]
    return Scores(["Total"], entries, from_grades=True)


def test_names(
    scores: Scores, values: list[str], template: list[list[str]] | None = None
) -> list[str]:
    """Each test's name on FAMS, from `--assessment CODE` or `LABEL=CODE`.

    A quiz defaults to `Quiz_<n>` by column order; a grade CSV's one test to the
    name every template row carries, and otherwise must be given.
    """
    labels = scores.labels
    names: dict[str, str] = {}
    if not scores.from_grades:
        names = {label: f"Quiz_{number}" for number, label in enumerate(labels, start=1)}
    elif template:
        at = quiz_scores._column_index(template[0], [TEST])
        found = {line[at].strip() for line in template[1:] if at < len(line) and line[at].strip()}
        if len(found) == 1:
            names[labels[0]] = found.pop()
    for value in values:
        label, sep, code = value.partition("=") if "=" in value else ("", "", value)
        label, code = label.strip(), code.strip()
        if not sep and len(labels) == 1:
            label = labels[0]
        if label not in labels or not code:
            raise UsageError(
                f"--assessment takes CODE for one test, or LABEL=CODE, got {value!r}",
                hint=f"tests: {', '.join(labels)}",
            )
        names[label] = code
    missing = [label for label in labels if label not in names]
    if missing:
        raise UsageError(
            "the test's code on FAMS is not known; pass --assessment",
            hint="e.g. --assessment 'Final Theory Exam_1', as the class's assessment list reads",
        )
    return [names[label] for label in labels]


# --- the sheet ---------------------------------------------------------------------


def build(
    scores: Scores,
    *,
    names: list[str],
    roster: Roster,
    topic_code: str | None,
    template: list[list[str]] | None = None,
    graded_only: bool = False,
) -> tuple[Sheet, Report]:
    marks = Marks(scores.entries, lambda e: e.std_id, lambda e: e.name)
    report = Report()
    # (account, name, topic, entry) per class trainee, in the class's order.
    listed: list[tuple[str, str, str, Entry | None]] = []

    if template is None:
        if not topic_code:
            raise UsageError("--topic-code is needed without a template, e.g. FR_JSKS_JCF")
        headers = list(HEADERS)
        at = {name: index for index, name in enumerate(HEADERS)}
        for trainee in roster.active:
            entry = marks.find(trainee, trainee.name)
            if entry is None and graded_only:
                continue
            if entry is None:
                report.zeroed.append(trainee.std_id)
            listed.append((trainee.fams_account, trainee.name, topic_code, entry))
    else:
        if not template or not template[0]:
            raise UsageError("the FAMS template's first sheet is empty")
        headers = list(template[0])
        at = {name: quiz_scores._column_index(headers, [name]) for name in HEADERS}
        seen: set[str] = set()
        skipped: list[str] = []
        for line in template[1:]:

            def cell(name: str, line: list[str] = line) -> str:
                index = at[name]
                return line[index].strip() if index < len(line) else ""

            account, name = cell(ACCOUNT), cell(NAME)
            if not account and not name:
                continue
            trainee, entry = marks.place(roster, account, name)
            who = trainee.std_id if trainee else (name or account)
            # A template stacks one row per test: the class is each trainee once.
            if who.lower() in seen:
                continue
            seen.add(who.lower())
            if entry is None and graded_only:
                skipped.append(who)
                continue
            if trainee is None:
                report.unmatched.append(who)
            if entry is None:
                report.zeroed.append(who)
            account = trainee.fams_account if trainee else account
            listed.append((account, name or trainee.name, cell(TOPIC) or topic_code or "", entry))
        if skipped:
            report.notes.append(f"no marks, left off (graded only): {', '.join(skipped)}")
        if any(not topic for _, _, topic, _ in listed):
            raise UsageError("the template has rows without a TopicCode; pass --topic-code")
    report.left_out = marks.unused()

    sheet = Sheet(headers=headers, rows=[])
    for test, name in enumerate(names):
        for account, full_name, topic, entry in listed:
            text = entry.marks[test] if entry else ""
            if entry and not text:
                report.missed.append((name, entry.std_id))
            mark = _mark(text) if text else 0.0
            row: list[str | float] = [""] * len(headers)
            row[at[ACCOUNT]] = account
            row[at[NAME]] = full_name
            row[at[TOPIC]] = topic
            row[at[TEST]] = name
            row[at[MARK]] = mark
            row[at[SCORE]] = mark
            row[at[TOTAL]] = 10.0
            sheet.rows.append(row)
    report.rows = len(sheet.rows)
    return sheet, report


def _mark(text: str) -> float:
    try:
        return float(text)
    except ValueError:
        raise UsageError(f"mark {text!r} is not a number") from None


def export_theory(
    scores: Scores,
    out: Path,
    *,
    roster: Roster,
    template: Path | None,
    topic_code: str | None,
    assessments: list[str],
    graded_only: bool = False,
) -> Report:
    rows = quiz_scores.read_sheet(template, 1) if template else None
    sheet, report = build(
        scores,
        names=test_names(scores, assessments, rows),
        roster=roster,
        topic_code=topic_code,
        template=rows,
        graded_only=graded_only,
    )
    write(sheet, out)
    return report


# --- writing the workbook ------------------------------------------------------------

_STYLES = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="{NS}">'
    '<numFmts count="1"><numFmt numFmtId="164" formatCode="0.0"/></numFmts>'
    '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
    '<fills count="2"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill></fills>'
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border>'
    "</borders>"
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>'
    "</cellStyleXfs>"
    '<cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" '
    'applyNumberFormat="1"/></cellXfs>'
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
    "</styleSheet>"
)


def _column(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def _cell(ref: str, value: str | float, *, header: bool) -> str:
    if isinstance(value, float):
        return f'<c r="{ref}" s="2"><v>{value:g}</v></c>'
    if value == "":
        return ""
    style = ' s="1"' if header else ""
    return f'<c r="{ref}" t="inlineStr"{style}><is><t>{escape(value)}</t></is></c>'


def write(sheet: Sheet, out: Path) -> None:
    lines = [sheet.headers, *sheet.rows]
    sheet_rows = "".join(
        f'<row r="{r}">'
        + "".join(_cell(f"{_column(c)}{r}", value, header=r == 1) for c, value in enumerate(line))
        + "</row>"
        for r, line in enumerate(lines, start=1)
    )
    sheet_xml = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{NS}"><sheetData>{sheet_rows}</sheetData></worksheet>'
    )
    write_workbook(out, SHEET, sheet_xml, _STYLES)
