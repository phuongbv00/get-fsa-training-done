"""Score a quiz platform's participant report.

Two sources. The report workbook's second sheet is the participant summary.
The Blooket leaderboard, copied from the browser as HTML, gives each player's
correct and incorrect counts but no question total, so `questions` supplies it:
a player who answered fewer questions than the quiz holds is scored out of the
quiz, and one who answered more (game modes repeat questions) is scored out of
what they answered. Both reduce to the same rule:

    expected_total = max(answered, correct + incorrect) + unattempted
    score = ceil(correct / expected_total * 10, 1 decimal)

`max(answered, correct + incorrect)` is a correction for reports whose
"Qs Answered" disagrees with correct + incorrect; taking the larger keeps a
trainee from being scored out of fewer questions than they actually saw.

The XLSX reader is hand-rolled over `zipfile` + `ElementTree` rather than
openpyxl, which keeps the whole grading pipeline dependency-free.

A trainee can appear more than once — a live game and a homework run of the same
quiz, or two reports pasted in parts. Their best attempt is kept.
"""

from __future__ import annotations

import csv
import html
import math
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from get_fsa_training_done.errors import UsageError

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


#: Blooket's class names carry a build hash (`ColumnTemplates_student__eQ3gW`),
#: so only their stable prefixes are matched.
_PLAYER = re.compile(r'class="[^"]*ColumnTemplates_student__[^"]*"[^>]*>([^<]+)<')
_BAR_TEXT = re.compile(r'class="[^"]*_barText__[^"]*"[^>]*>\s*([\d,]+)\s*<')
_CORRECT_BAR = "_correctAnswersBar__"
_ICON = re.compile(r"<svg\b.*?</svg>", re.DOTALL)
LEADERBOARD_HEADERS = ["Nickname", "Qs Answered", "Correct", "Incorrect", "Unattempted"]


def read_leaderboard(path: Path, questions: int) -> list[list[str]]:
    """A Blooket leaderboard paste as report rows, so `score` can treat both alike.

    Each player's block holds their name, then an accuracy bar with the correct
    count inside the green part and the incorrect count after it. A player with
    no wrong answers, or no right ones, has only one number, and which one it
    is depends on whether the green bar is there.
    """
    if questions < 1:
        raise UsageError("--questions must be the number of questions in the quiz")
    if not path.is_file():
        raise UsageError(f"leaderboard paste not found: {path}")
    # The bar labels carry an icon before the count; drop the icons so the
    # count is the label's first text.
    page = _ICON.sub("", path.read_text(encoding="utf-8"))
    players = list(_PLAYER.finditer(page))
    if not players:
        raise UsageError(
            f"{path} holds no Blooket leaderboard players",
            hint="copy the leaderboard element's outer HTML from the report page",
        )
    rows = [list(LEADERBOARD_HEADERS)]
    for index, player in enumerate(players):
        end = players[index + 1].start() if index + 1 < len(players) else len(page)
        block = page[player.end() : end]
        numbers = [int(n.replace(",", "")) for n in _BAR_TEXT.findall(block)]
        if len(numbers) >= 2:
            correct, incorrect = numbers[0], numbers[1]
        elif len(numbers) == 1:
            correct, incorrect = (numbers[0], 0) if _CORRECT_BAR in block else (0, numbers[0])
        else:
            correct, incorrect = 0, 0
        answered = correct + incorrect
        rows.append(
            [
                html.unescape(player.group(1)).strip(),
                str(answered),
                str(correct),
                str(incorrect),
                str(max(0, questions - answered)),
            ]
        )
    return rows


def score(
    rows: list[list[str]],
    roster: Roster | None,
    aliases: dict[str, str] | None = None,
) -> QuizResult:
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

    aliases = {key.strip().lower(): value.strip() for key, value in (aliases or {}).items()}
    result = QuizResult(rows=[["Std ID", "score"]])
    best: dict[str, float] = {}
    order: list[str] = []
    for row in rows[1:]:
        nickname = cell(row, nickname_at).strip()
        if not nickname:
            continue
        nickname = aliases.get(nickname.lower(), nickname)

        if roster is not None:
            trainee = roster.get(nickname)
            if trainee is None:
                # Report it rather than dropping it silently: a trainee who
                # typed their nickname loosely still sat the quiz, and someone
                # has to reconcile it by hand.
                if nickname not in result.unmatched:
                    result.unmatched.append(nickname)
                continue
            if trainee.dropped:
                if trainee.std_id not in result.dropped:
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
        key = nickname.lower()
        if key not in best:
            order.append(nickname)
            best[key] = value
        else:
            best[key] = max(best[key], value)

    result.rows += [[nickname, f"{best[nickname.lower()]:.1f}"] for nickname in order]
    return result


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        csv.writer(handle).writerows(rows)
