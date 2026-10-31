"""A module's quiz scores as the workbook FAMS imports.

FAMS takes one row per trainee per test, on one sheet:

    Email or Account, Full Name, TopicCode, TestName, Final Mark (/10), Score, Total Score

The rows come from one of two places:

- **the class template downloaded from FAMS** — it decides who is in the class.
  A trainee the scores have but the template lacks is left out (FAMS rejects
  anyone not enrolled, or whose status does not allow a mark) and reported; a
  template trainee with no scores is written with zeros and reported. The
  template's header row is kept as it is, extra columns and all.
- **the roster**, when there is no template: every active trainee.

Quizzes are stacked, one block of rows per quiz, named `Quiz_1`, `Quiz_2`, …
in column order unless named otherwise. The account column carries the FPT
account id — the roster's `Account` column overrides it for a trainee FAMS
knows by another account, such as a CPL trainee's personal email — never the
email a template ships with. FAMS refuses a blank mark, so a quiz a trainee
did not sit is written as 0.

Like the reader in `quiz_scores`, the writer is `zipfile` and hand-written
XML, so the export needs no spreadsheet library.
"""

from __future__ import annotations

import csv
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

from get_fsa_training_done.errors import UsageError

from . import quiz_scores
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


@dataclass
class Export:
    headers: list[str]
    rows: list[list[str | float]]
    sheet: str = SHEET
    #: Scored trainees the template does not list, so left out.
    left_out: list[str] = field(default_factory=list)
    #: Template trainees with no scores, written with zeros.
    zeroed: list[str] = field(default_factory=list)
    #: (test name, trainee id) pairs written as 0 because the quiz was missed.
    missed: list[tuple[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class _Person:
    std_id: str
    name: str
    account: str
    marks: tuple[str, ...]


def _key(text: str) -> str:
    """Names compared as people write them: NFC, case and spacing ignored."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text or "")).strip().casefold()


def read_scores(path: Path) -> tuple[list[str], list[list[str]]]:
    """A `grade quiz-module` CSV: its quiz labels and its rows."""
    if not path.is_file():
        raise UsageError(f"score CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if not rows or rows[0][:3] != ["No", "ID", "Name"] or len(rows[0]) < 4:
        raise UsageError(f"{path} is not `grade quiz-module` output (No, ID, Name, <quiz>…)")
    return rows[0][3:], [row for row in rows[1:] if len(row) > 1 and row[1].strip()]


def parse_test_names(labels: list[str], values: list[str]) -> list[str]:
    names = {label: f"Quiz_{number}" for number, label in enumerate(labels, start=1)}
    for value in values:
        label, sep, name = value.partition("=")
        if not sep or label.strip() not in names or not name.strip():
            raise UsageError(
                f"--test-name takes LABEL=NAME for a quiz in the score CSV, got {value!r}",
                hint=f"quizzes: {', '.join(labels)}",
            )
        names[label.strip()] = name.strip()
    return [names[label] for label in labels]


def _people(rows: list[list[str]], quizzes: int, roster: Roster | None) -> list[_Person]:
    people = []
    for row in rows:
        std_id = row[1].strip()
        trainee = roster.get(std_id) if roster else None
        marks = tuple((row[3 + i] if 3 + i < len(row) else "").strip() for i in range(quizzes))
        people.append(
            _Person(
                std_id=std_id,
                name=row[2].strip(),
                account=trainee.fams_account if trainee else std_id,
                marks=marks,
            )
        )
    return people


def _mark(text: str) -> float:
    try:
        return float(text)
    except ValueError:
        raise UsageError(f"score {text!r} is not a number") from None


def build(
    labels: list[str],
    rows: list[list[str]],
    *,
    test_names: list[str],
    topic_code: str | None,
    roster: Roster | None = None,
    template: list[list[str]] | None = None,
) -> Export:
    people = _people(rows, len(labels), roster)

    if template is None:
        if not topic_code:
            raise UsageError("--topic-code is needed without a template, e.g. FR_JSKS_JCF")
        export = Export(headers=list(HEADERS), rows=[])
        at = {name: index for index, name in enumerate(HEADERS)}
        listed = [(person, person.name, topic_code) for person in people]
    else:
        if not template or not template[0]:
            raise UsageError("the FAMS template's first sheet is empty")
        headers = template[0]
        at = {name: quiz_scores._column_index(headers, [name]) for name in HEADERS}
        export = Export(headers=list(headers), rows=[])
        by_account = {}
        for person in people:
            by_account[person.std_id.lower()] = person
            by_account[person.account.lower()] = person
        by_name = {_key(person.name): person for person in people}
        listed, seen = [], set()
        for line in template[1:]:

            def cell(name: str, line: list[str] = line) -> str:
                index = at[name]
                return line[index].strip() if index < len(line) else ""

            account, name = cell(ACCOUNT), cell(NAME)
            if not account and not name:
                continue
            person = by_account.get(account.lower()) or by_name.get(_key(name))
            if person is None:
                person = _Person(std_id=account or name, name=name, account=account, marks=())
                export.zeroed.append(name or account)
            if person.std_id in seen:
                continue
            seen.add(person.std_id)
            listed.append((person, name or person.name, cell(TOPIC) or topic_code))
        if any(not topic for _, _, topic in listed):
            raise UsageError("the template has rows without a TopicCode; pass --topic-code")
        export.left_out = [person.std_id for person in people if person.std_id not in seen]

    width = len(export.headers)
    for quiz, test_name in enumerate(test_names):
        for person, name, topic in listed:
            text = person.marks[quiz] if quiz < len(person.marks) else ""
            if not text and person.marks:
                export.missed.append((test_name, person.std_id))
            mark = _mark(text) if text else 0.0
            row: list[str | float] = [""] * width
            row[at[ACCOUNT]] = person.account
            row[at[NAME]] = name
            row[at[TOPIC]] = topic
            row[at[TEST]] = test_name
            row[at[MARK]] = mark
            row[at[SCORE]] = mark
            row[at[TOTAL]] = 10.0
            export.rows.append(row)
    return export


# --- writing the workbook ------------------------------------------------------

_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"


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


def write(export: Export, out: Path) -> None:
    lines = [export.headers, *export.rows]
    sheet_rows = "".join(
        f'<row r="{r}">'
        + "".join(_cell(f"{_column(c)}{r}", value, header=r == 1) for c, value in enumerate(line))
        + "</row>"
        for r, line in enumerate(lines, start=1)
    )
    parts = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" '
            'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{_PKG}">'
            f'<Relationship Id="rId1" Type="{_REL}/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        ),
        "xl/workbook.xml": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<workbook xmlns="{_NS}" xmlns:r="{_REL}"><sheets>'
            f'<sheet name="{escape(export.sheet)}" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{_PKG}">'
            f'<Relationship Id="rId1" Type="{_REL}/worksheet" Target="worksheets/sheet1.xml"/>'
            f'<Relationship Id="rId2" Type="{_REL}/styles" Target="styles.xml"/>'
            "</Relationships>"
        ),
        "xl/styles.xml": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="{_NS}">'
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
        ),
        "xl/worksheets/sheet1.xml": (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<worksheet xmlns="{_NS}"><sheetData>{sheet_rows}</sheetData></worksheet>'
        ),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, body in parts.items():
            archive.writestr(name, body)
