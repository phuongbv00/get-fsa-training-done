"""Score a quiz platform's participant report.

The workbook's second sheet is the participant summary. Scoring is:

    expected_total = max(answered, correct + incorrect) + unattempted
    score = ceil(correct / expected_total * 10, 1 decimal)

`max(answered, correct + incorrect)` is a correction for reports whose
"Qs Answered" disagrees with correct + incorrect; taking the larger keeps a
trainee from being scored out of fewer questions than they actually saw.

The XLSX reader is hand-rolled over `zipfile` + `ElementTree` rather than
openpyxl, which keeps the whole grading pipeline dependency-free.
"""

from __future__ import annotations

import csv
import math
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from fsa_trainer_skills.errors import UsageError

from .roster import Roster

MAIN_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

NICKNAME_COLUMN = ["Nickname"]
ANSWERED_COLUMN = ["Qs Answered", "Questions Answered"]
CORRECT_COLUMN = ["Correct"]
INCORRECT_COLUMN = ["Incorrect"]
UNATTEMPTED_COLUMN = ["Unattempted"]


@dataclass
class QuizResult:
    rows: list[list[str]]
    unmatched: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)

    @property
    def scored(self) -> int:
        return max(0, len(self.rows) - 1)


def _rich_text(node) -> str:
    return "".join(part.text or "" for part in node.findall(".//m:t", MAIN_NS))


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [_rich_text(item) for item in root.findall("m:si", MAIN_NS)]


def _sheet_path(archive: zipfile.ZipFile, sheet_index: int) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    sheets = workbook.findall("m:sheets/m:sheet", MAIN_NS)
    if sheet_index < 1 or sheet_index > len(sheets):
        raise UsageError(
            f"workbook has {len(sheets)} sheet(s); --sheet-index {sheet_index} is out of range"
        )
    relationship = sheets[sheet_index - 1].attrib[REL_ID]
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    target = targets.get(relationship)
    if not target:
        raise UsageError(f"could not resolve workbook relationship {relationship}")
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join("xl", target))


def _column_number(reference: str | None) -> int:
    match = re.match(r"([A-Z]+)", reference or "")
    if not match:
        return 1
    number = 0
    for character in match.group(1):
        number = number * 26 + ord(character) - ord("A") + 1
    return number


def _cell_value(cell, shared: list[str]) -> str:
    kind = cell.attrib.get("t")
    if kind == "inlineStr":
        inline = cell.find("m:is", MAIN_NS)
        return _rich_text(inline) if inline is not None else ""
    value = cell.find("m:v", MAIN_NS)
    if value is None:
        return ""
    text = value.text or ""
    if kind == "s":
        return shared[int(text)] if text else ""
    if kind == "b":
        return "TRUE" if text == "1" else "FALSE"
    return text


def read_sheet(path: Path, sheet_index: int) -> list[list[str]]:
    if not path.is_file():
        raise UsageError(f"quiz report not found: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            shared = _shared_strings(archive)
            sheet = ET.fromstring(archive.read(_sheet_path(archive, sheet_index)))
    except zipfile.BadZipFile:
        raise UsageError(f"{path} is not a readable .xlsx workbook") from None

    rows: list[list[str]] = []
    for row in sheet.findall("m:sheetData/m:row", MAIN_NS):
        cells: list[str] = []
        for cell in row.findall("m:c", MAIN_NS):
            index = _column_number(cell.attrib.get("r")) - 1
            while len(cells) <= index:
                cells.append("")
            cells[index] = _cell_value(cell, shared)
        while cells and cells[-1] == "":
            cells.pop()
        rows.append(cells)
    return rows


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())


def _column_index(headers: list[str], names: list[str]) -> int:
    mapping = {_normalise(name): index for index, name in enumerate(headers)}
    for name in names:
        key = _normalise(name)
        if key in mapping:
            return mapping[key]
    available = ", ".join(header for header in headers if header)
    raise UsageError(
        f"quiz report is missing a required column ({', '.join(names)})",
        hint=f"columns present: {available}",
    )


def _number(value: str) -> float:
    text = str(value or "").strip().replace(",", "")
    if text.endswith("%"):
        text = text[:-1]
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _round_up(value: float) -> float:
    return math.ceil((value * 10) - 1e-12) / 10


def score(rows: list[list[str]], roster: Roster | None) -> QuizResult:
    if not rows:
        raise UsageError("quiz report sheet is empty")

    headers = rows[0]
    nickname_at = _column_index(headers, NICKNAME_COLUMN)
    answered_at = _column_index(headers, ANSWERED_COLUMN)
    correct_at = _column_index(headers, CORRECT_COLUMN)
    incorrect_at = _column_index(headers, INCORRECT_COLUMN)
    unattempted_at = _column_index(headers, UNATTEMPTED_COLUMN)

    def cell(row: list[str], index: int) -> str:
        return row[index] if index < len(row) else ""

    result = QuizResult(rows=[["Std ID", "score"]])
    for row in rows[1:]:
        nickname = cell(row, nickname_at).strip()
        if not nickname:
            continue

        if roster is not None:
            trainee = roster.get(nickname)
            if trainee is None:
                # Report it rather than dropping it silently: a trainee who
                # typed their nickname loosely still sat the quiz, and someone
                # has to reconcile it by hand.
                result.unmatched.append(nickname)
                continue
            if trainee.dropped:
                result.dropped.append(trainee.std_id)
                continue
            nickname = trainee.std_id

        answered = _number(cell(row, answered_at))
        correct = _number(cell(row, correct_at))
        incorrect = _number(cell(row, incorrect_at))
        unattempted = _number(cell(row, unattempted_at))

        expected_total = max(answered, correct + incorrect) + unattempted
        value = (
            0.0
            if expected_total == 0
            else _round_up(min(10.0, max(0.0, correct / expected_total * 10)))
        )
        result.rows.append([nickname, f"{value:.1f}"])

    return result


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        csv.writer(handle).writerows(rows)
