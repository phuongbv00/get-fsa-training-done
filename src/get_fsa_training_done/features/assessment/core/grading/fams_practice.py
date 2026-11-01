"""Marks as FAMS's practice mark template: one row per trainee, a mark per task.

The assignments and the practice exam take this form, one sheet:

    B3 Topic:       C3 FR_JSKS_JCF
    B4 Assessment:  C4 Assignments_1        — the assessment's code on FAMS
    B5 Marker:      C5 PhuongBV3
    B6 Date:        C6 31/10/2026
    row 9   Account | Full Name | <mark> | Comment | Q1 … Qn | Bonus
    row 11  Passing Score | 6 |          |  w1 … wn | 0      — the task weights
    row 12  the worked example: every Q at 10, the mark formula
    row 13… one row per trainee

The marks are a grade CSV's (`grade aggregate` or `merge-retake`). Who is in
the class, which account a row carries and why nothing is blank are the rules
in `fams`; a template trainee with no grade row also gets the
missing-submission comment. The template's comments say its label cells must
not move, so its layout is found by those labels and edited in place with
`features/common/xlsx`; every part the export does not write is copied
through. Without a template the same form is generated, one row per active
roster trainee.

The template's question columns are laid out again to the grade CSV's tasks —
`Q1..Qn` in task order, then `Bonus` — so a three-question form carries a
six-task assignment. The mark is the template's `SUMPRODUCT` over the weights
row, written with its value cached: an importer that reads cells rather than
recalculating sees the mark, not an empty formula.
"""

from __future__ import annotations

import csv
import datetime as _dt
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.common.xlsx import refs
from get_fsa_training_done.features.common.xlsx.package import XlsxPackage
from get_fsa_training_done.features.common.xlsx.sheetxml import Sheet, q

from .fams import NS, Marks, Report, write_workbook
from .roster import Roster

TOPIC = "Topic:"
ASSESSMENT = "Assessment:"
MARKER = "Marker:"
DATE = "Date:"
NAME = "Full Name"
PASSING = "Passing Score"
BONUS = "Bonus"
DATE_FORMAT = "%d/%m/%Y"
MISSING_COMMENT = "Not submitted."

_WEIGHT = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*%\s*\)")
_QUESTION = re.compile(r"^Q\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class Task:
    label: str
    weight: float


@dataclass(frozen=True)
class Grade:
    std_id: str
    name: str
    comment: str
    scores: tuple[float, ...]


@dataclass
class Layout:
    """Where the form's parts are, found by their labels."""

    info: dict[str, str]  # label -> the cell holding its value
    header_row: int
    weights_row: int
    example_row: int
    first_row: int
    last_row: int
    account_col: int
    name_col: int
    mark_col: int
    comment_col: int
    question_cols: list[int]
    bonus_col: int


# --- the grade CSV ---------------------------------------------------------------


def read_grades(path: Path) -> tuple[list[Task], list[Grade]]:
    """A `grade aggregate` (or `merge-retake`) CSV: its weighted tasks and rows."""
    if not path.is_file():
        raise UsageError(f"grade CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if not rows or rows[0][:3] != ["Std ID", "Name", "Comment"] or rows[0][-1] != "Total":
        raise UsageError(
            f"{path} is not `grade aggregate` output (Std ID, Name, Comment, T…, Total)"
        )
    tasks = []
    for label in rows[0][3:-1]:
        match = _WEIGHT.search(label)
        if not match:
            raise UsageError(
                f"task column {label!r} carries no weight",
                hint="a merged retake whose papers had different tasks has none; "
                "export each attempt's own grade CSV instead",
            )
        tasks.append(Task(label=label, weight=float(match.group(1))))
    if not tasks:
        raise UsageError(f"{path} has no task columns")
    grades = []
    for row in rows[1:]:
        if len(row) < 3 or not row[0].strip():
            continue
        cells = row[3 : 3 + len(tasks)]
        try:
            scores = tuple(float(cell) if cell.strip() else 0.0 for cell in cells)
        except ValueError:
            raise UsageError(f"{row[0]}: a task score is not a number: {cells}") from None
        grades.append(Grade(row[0].strip(), row[1].strip(), row[2].strip(), scores))
    return tasks, grades


def mark(tasks: list[Task], scores: tuple[float, ...]) -> float:
    """What the form's SUMPRODUCT computes: the bonus weighs 0."""
    return sum(t.weight * s for t, s in zip(tasks, scores, strict=True)) / sum(
        t.weight for t in tasks
    )


# --- reading the form ------------------------------------------------------------


def _texts(package: XlsxPackage, sheet: Sheet) -> dict[str, str]:
    shared = package.shared_strings()
    texts = {}
    for row in sheet.sheet_data.findall(q("row")):
        for cell in row.findall(q("c")):
            ref = cell.get("r")
            if not ref:
                continue
            if cell.get("t") == "s":
                value = cell.find(q("v"))
                text = shared[int(value.text)] if value is not None and value.text else ""
            elif cell.get("t") == "inlineStr":
                text = "".join(node.text or "" for node in cell.iter(q("t")))
            else:
                value = cell.find(q("v"))
                text = value.text if value is not None and value.text else ""
            if text.strip():
                texts[ref] = text.strip()
    return texts


def locate(package: XlsxPackage, sheet: Sheet) -> Layout:
    texts = _texts(package, sheet)
    at: dict[str, tuple[int, int]] = {}
    for ref, text in texts.items():
        at.setdefault(text.casefold(), refs.split(ref))

    def find(label: str) -> tuple[int, int]:
        if label.casefold() not in at:
            raise UsageError(
                f"the template has no {label!r} cell",
                hint="pass the practice mark template FAMS gives for an assignment or exam",
            )
        return at[label.casefold()]

    info = {}
    for label in (TOPIC, ASSESSMENT, MARKER, DATE):
        column, row = find(label)
        info[label] = refs.cell(column + 1, row)

    name_col, header_row = find(NAME)
    header = {
        column: texts[ref].casefold()
        for ref in texts
        for column, row in [refs.split(ref)]
        if row == header_row
    }
    account = [c for c, t in header.items() if "account" in t or "email" in t]
    comment = [c for c, t in header.items() if "comment" in t]
    questions = sorted(c for c, t in header.items() if _QUESTION.match(t))
    bonus = [c for c, t in header.items() if t == BONUS.casefold()]
    if not account or not comment or not questions or not bonus:
        raise UsageError(
            f"row {header_row} of the template lacks an Account, Comment, Q1… or Bonus header"
        )
    _, weights_row = find(PASSING)
    example_row = weights_row + 1
    first_row = example_row + 1
    last_row = first_row - 1
    for ref in texts:
        column, row = refs.split(ref)
        if row >= first_row and column in (account[0], name_col):
            last_row = max(last_row, row)
    return Layout(
        info=info,
        header_row=header_row,
        weights_row=weights_row,
        example_row=example_row,
        first_row=first_row,
        last_row=last_row,
        account_col=account[0],
        name_col=name_col,
        mark_col=name_col + 1,
        comment_col=comment[0],
        question_cols=questions,
        bonus_col=bonus[0],
    )


# --- laying the question columns out again ---------------------------------------


def _source_question(k: int, new: int, old: int) -> int:
    """Which old question column lends new column `k` its style: the first and
    last keep their edges, the ones between take a middle column's."""
    if k == 0:
        return 0
    if k == new - 1:
        return old - 1
    return max(0, min(k, old - 2))


def relay(sheet: Sheet, layout: Layout, count: int) -> None:
    """Make the question block `count` columns wide, then Bonus.

    Each new cell takes the style of the old column it stands for, cells right
    of the block shift with it, and the header merges follow their columns.
    """
    first, old = layout.question_cols[0], len(layout.question_cols)
    old_bonus = layout.bonus_col
    shift = (first + count) - old_bonus
    sources = [first + _source_question(k, count, old) for k in range(count)] + [old_bonus]

    for row in sheet.sheet_data.findall(q("row")):
        row.attrib.pop("spans", None)
        cells = {refs.split(c.get("r"))[0]: c for c in row.findall(q("c"))}
        number = int(row.get("r"))
        styles = {column: cell.get("s") for column, cell in cells.items()}
        for column, cell in cells.items():
            if first <= column <= old_bonus:
                row.remove(cell)
            elif column > old_bonus:
                cell.set("r", refs.cell(column + shift, number))
        for k, source in enumerate(sources):
            if source in styles:
                attrs = {"r": refs.cell(first + k, number)}
                if styles[source] is not None:
                    attrs["s"] = styles[source]
                row.append(ET.Element(q("c"), attrs))
        ordered = sorted(row.findall(q("c")), key=lambda c: refs.split(c.get("r"))[0])
        for cell in ordered:
            row.remove(cell)
        row.extend(ordered)

    merges = []
    spans: dict[int, list[tuple[int, int]]] = {}
    for value in sheet.merges():
        (c1, r1), (c2, r2) = (refs.split(part) for part in value.split(":"))
        if c1 == c2 and first <= c1 <= old_bonus:
            spans.setdefault(c1, []).append((r1, r2))
            continue
        if c1 > old_bonus:
            c1 += shift
        if c2 >= old_bonus:
            c2 += shift
        merges.append(f"{refs.cell(c1, r1)}:{refs.cell(c2, r2)}")
    for k, source in enumerate(sources):
        for r1, r2 in spans.get(source, []):
            merges.append(f"{refs.cell(first + k, r1)}:{refs.cell(first + k, r2)}")
    sheet.set_merges(merges)

    cols = sheet.root.find(q("cols"))
    if cols is not None:
        widths = {}
        for col in list(cols):
            for column in range(int(col.get("min")), int(col.get("max")) + 1):
                widths[column] = dict(col.attrib)
            cols.remove(col)
        laid = {c: a for c, a in widths.items() if c < first}
        laid.update({c + shift: a for c, a in widths.items() if c > old_bonus})
        for k, source in enumerate(sources):
            if source in widths:
                laid[first + k] = widths[source]
        for column in sorted(laid):
            attrs = dict(laid[column], min=str(column), max=str(column))
            cols.append(ET.Element(q("col"), attrs))

    layout.question_cols = list(range(first, first + count))
    layout.bonus_col = first + count
    layout.comment_col += shift if layout.comment_col > old_bonus else 0


# --- writing ---------------------------------------------------------------------


def _formula(layout: Layout, row: int) -> str:
    first = refs.column_letter(layout.question_cols[0])
    last = refs.column_letter(layout.bonus_col)
    weights = f"${first}${layout.weights_row}:${last}${layout.weights_row}"
    return f"SUMPRODUCT({weights},{first}{row}:{last}{row})/SUM({weights})"


def _set_mark(sheet: Sheet, layout: Layout, row: int, value: float) -> None:
    ref = refs.cell(layout.mark_col, row)
    sheet.set_formula(ref, _formula(layout, row))
    cached = ET.SubElement(sheet.cell(ref), q("v"))
    cached.text = repr(round(value, 10))


def fill(
    package: XlsxPackage,
    sheet_name: str,
    tasks: list[Task],
    grades: list[Grade],
    *,
    roster: Roster,
    info: dict[str, str | None],
    missing_comment: str,
    mark_label: str | None = None,
) -> Report:
    sheet = package.sheet(sheet_name)
    layout = locate(package, sheet)
    export = Report()
    if len(layout.question_cols) != len(tasks):
        export.notes.append(
            f"the template's {len(layout.question_cols)} question column(s) laid out again"
        )
        relay(sheet, layout, len(tasks))
    texts = _texts(package, sheet)

    for label, ref in layout.info.items():
        value = info.get(label) or texts.get(ref, "")
        if label != DATE and not value:
            raise UsageError(
                f"{label.rstrip(':')} is blank in the template and was not given",
                hint="pass --topic-code, --assessment and --marker",
            )
        if info.get(label):
            sheet.set_text(ref, value)
        export.info[label] = value

    header = layout.header_row
    if mark_label:
        sheet.set_text(refs.cell(layout.mark_col, header), mark_label)
    for k, task in enumerate(tasks):
        column = layout.question_cols[k]
        sheet.set_text(refs.cell(column, header), f"Q{k + 1}")
        sheet.set_number(refs.cell(column, layout.weights_row), task.weight)
        sheet.set_number(refs.cell(column, layout.example_row), 10)
    sheet.set_text(refs.cell(layout.bonus_col, header), BONUS)
    sheet.set_number(refs.cell(layout.bonus_col, layout.weights_row), 0)
    sheet.clear(refs.cell(layout.bonus_col, layout.example_row))
    _set_mark(sheet, layout, layout.example_row, 10.0)

    marks = Marks(grades, lambda g: g.std_id, lambda g: g.name)
    for row in range(layout.first_row, layout.last_row + 1):
        account = texts.get(refs.cell(layout.account_col, row), "")
        name = texts.get(refs.cell(layout.name_col, row), "")
        if not account and not name:
            continue
        trainee, grade = marks.place(roster, account, name)
        if trainee is not None:
            sheet.set_text(refs.cell(layout.account_col, row), trainee.fams_account)
        else:
            export.unmatched.append(name or account)
        if grade is None:
            export.zeroed.append(trainee.std_id if trainee else name or account)
            scores = (0.0,) * len(tasks)
            comment = missing_comment
        else:
            scores, comment = grade.scores, grade.comment
        for k, score in enumerate(scores):
            sheet.set_number(refs.cell(layout.question_cols[k], row), score)
        sheet.set_number(refs.cell(layout.bonus_col, row), 0)
        _set_mark(sheet, layout, row, mark(tasks, scores))
        sheet.set_text(refs.cell(layout.comment_col, row), comment)
        export.rows += 1
    export.left_out = marks.unused()

    package.write_sheet(sheet_name, sheet)
    package.drop_calc_chain()
    package.force_full_recalc()
    return export


def export_practice(
    grades_csv: Path,
    out: Path,
    *,
    roster: Roster,
    template: Path | None,
    topic_code: str | None,
    assessment: str | None,
    marker: str | None,
    date: str | None,
    pass_mark: float,
    missing_comment: str = MISSING_COMMENT,
    mark_label: str | None = None,
) -> Report:
    tasks, grades = read_grades(grades_csv)
    info = {
        TOPIC: topic_code,
        ASSESSMENT: assessment,
        MARKER: marker,
        DATE: date or _dt.date.today().strftime(DATE_FORMAT),
    }
    if template is None:
        flags = {"--topic-code": topic_code, "--assessment": assessment, "--marker": marker}
        missing = [flag for flag, value in flags.items() if not value]
        if missing:
            raise UsageError(f"without a template, {', '.join(missing)} must be given")
        write_form(out, roster, tasks, pass_mark=pass_mark, mark_label=mark_label or "Mark")
        package = XlsxPackage(out)
    else:
        package = XlsxPackage(template)
    sheet_name = package.sheet_names()[0]
    result = fill(
        package,
        sheet_name,
        tasks,
        grades,
        roster=roster,
        info=info,
        missing_comment=missing_comment,
        mark_label=mark_label if template is not None else None,
    )
    package.save(out)
    return result


# --- the form, generated ---------------------------------------------------------

#: The notes FAMS's own form carries beside the header block.
NOTES = [
    "Lưu ý:",
    "- Giảng viên điền (row 11) và chấm theo barem đã đưa ra trong đề thi",
    "- Bài làm của học viên cần phải có comment",
    "- Giảng viên chấm theo thang điểm 10 với từng câu hỏi",
]

# cellXfs, in order: default, title, label, header, cell, mark, comment
_STYLES = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="{NS}">'
    '<numFmts count="1"><numFmt numFmtId="164" formatCode="0.0"/></numFmts>'
    '<fonts count="3"><font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="14"/><name val="Calibri"/></font></fonts>'
    '<fills count="3"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/></patternFill></fill></fills>'
    '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>'
    '<border><left style="thin"/><right style="thin"/><top style="thin"/><bottom style="thin"/>'
    "<diagonal/></border></borders>"
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="7"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" '
    'applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" '
    'wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>'
    '<xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" '
    'applyBorder="1"/>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" '
    'applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf></cellXfs>'
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
    "</styleSheet>"
)
_TITLE, _LABEL, _HEAD, _CELL, _MARK, _COMMENT = range(1, 7)


def _cell(ref: str, value: str | float | None, style: int) -> str:
    if value is None or value == "":
        return f'<c r="{ref}" s="{style}"/>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}" s="{style}"><v>{value:g}</v></c>'
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'


def write_form(
    out: Path, roster: Roster, tasks: list[Task], *, pass_mark: float, mark_label: str
) -> None:
    """The practice mark template FAMS gives, laid out cell for cell, for the active roster."""
    count = len(tasks)
    first_q, bonus = 6, 6 + count
    rows: dict[int, list[str]] = {}

    def put(column: int, row: int, value, style: int) -> None:
        rows.setdefault(row, []).append(_cell(refs.cell(column, row), value, style))

    put(2, 1, "MARKS TABLE", _TITLE)
    for offset, note in enumerate(NOTES):
        put(4, 2 + offset, note, _LABEL if offset == 0 else 0)
    for row, label in zip(range(3, 7), (TOPIC, ASSESSMENT, MARKER, DATE), strict=True):
        put(2, row, label, _LABEL)
        put(3, row, "", 0)
    put(1, 8, "#", _HEAD)
    put(2, 8, "Roles Applied:", _HEAD)
    put(3, 8, "", _HEAD)
    headers = ["Account Fsoft Or Personal Email", NAME, mark_label, "Comment"]
    headers += [f"Q{k + 1}" for k in range(count)] + [BONUS]
    for row in (9, 10):
        put(1, row, "", _HEAD)
        for column, text in enumerate(headers, start=2):
            put(column, row, text if row == 9 else "", _HEAD)
    put(1, 11, "", _HEAD)
    put(2, 11, "", _CELL)
    put(3, 11, PASSING, _LABEL)
    put(4, 11, pass_mark, _CELL)
    put(5, 11, "", _CELL)
    for column in range(first_q, bonus + 1):
        put(column, 11, 0, _CELL)
    put(1, 12, 0, _CELL)
    put(2, 12, "Chấm điểm theo ví dụ của dòng này", _CELL)
    put(3, 12, "", _CELL)
    for column in (4, 5, *range(first_q, bonus + 1)):
        put(column, 12, "", _MARK if column == 4 else _CELL)
    for number, trainee in enumerate(roster.active, start=1):
        row = 12 + number
        put(1, row, number, _CELL)
        put(2, row, trainee.fams_account, _CELL)
        put(3, row, trainee.name, _CELL)
        put(4, row, "", _MARK)
        put(5, row, "", _COMMENT)
        for column in range(first_q, bonus + 1):
            put(column, row, "", _CELL)

    merges = ["A8:A11", "B8:C8", "B12:C12"]
    merges += [f"{refs.column_letter(c)}9:{refs.column_letter(c)}10" for c in range(2, bonus + 1)]
    widths = {1: 4, 2: 26, 3: 24, 4: 10, 5: 60, **{c: 6 for c in range(first_q, bonus + 1)}}
    sheet = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{NS}">'
        "<cols>"
        + "".join(
            f'<col min="{c}" max="{c}" width="{w}" customWidth="1"/>' for c, w in widths.items()
        )
        + "</cols><sheetData>"
        + "".join(f'<row r="{r}">{"".join(rows[r])}</row>' for r in sorted(rows))
        + f'</sheetData><mergeCells count="{len(merges)}">'
        + "".join(f'<mergeCell ref="{m}"/>' for m in merges)
        + "</mergeCells></worksheet>"
    )
    write_workbook(out, "Sheet1", sheet, _STYLES)
