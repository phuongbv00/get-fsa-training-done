"""Blooket import CSV.

Two quirks of Blooket's importer drive everything here:

* The title row must serialise as **eight** fields —
  `Blooket Import Template,,,,,,,` — because Blooket sniffs the delimiter from
  it. A single-cell title row makes it guess wrong, and the failure surfaces
  much later as `Invalid Opening Quote` on the first correctly quoted field.
* Line endings must be CRLF throughout, with no BOM.

Neither is discoverable from the error message you get when you break it, which
is exactly why this is generated rather than hand-written.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from ..verify.common import BLOOKET_COLUMNS, MAX_TIME_LIMIT_SECONDS
from .master import Question

TITLE_ROW = ["Blooket Import Template", "", "", "", "", "", "", ""]
#: Blooket shows four options per question at most.
BLOOKET_OPTIONS = 4


def _time_limit(question: Question) -> str:
    raw = question.time_limit.strip()
    if raw.isdigit() and int(raw) > MAX_TIME_LIMIT_SECONDS:
        return str(MAX_TIME_LIMIT_SECONDS)
    return raw


def rows(questions: list[Question]) -> list[list[str]]:
    out = [TITLE_ROW, list(BLOOKET_COLUMNS)]
    for index, question in enumerate(questions, start=1):
        options = question.options[:BLOOKET_OPTIONS]
        options += [""] * (BLOOKET_OPTIONS - len(options))
        out.append(
            [
                str(index),
                question.text,
                *options,
                _time_limit(question),
                question.correct_field,
            ]
        )
    return out


def render(questions: list[Question]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerows(rows(questions))
    return buffer.getvalue().encode("utf-8")


def write(questions: list[Question], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(render(questions))
    return len(questions)


def warnings(questions: list[Question]) -> list[str]:
    notes = []
    over = [q.number for q in questions if len(q.options) > BLOOKET_OPTIONS]
    if over:
        notes.append(
            f"{len(over)} question(s) have more than {BLOOKET_OPTIONS} options; "
            f"Blooket shows only the first {BLOOKET_OPTIONS} (questions "
            + ", ".join(str(n) for n in over[:5])
            + ("..." if len(over) > 5 else "")
            + ")"
        )
    capped = [
        q.number
        for q in questions
        if q.time_limit.strip().isdigit() and int(q.time_limit) > MAX_TIME_LIMIT_SECONDS
    ]
    if capped:
        notes.append(
            f"{len(capped)} question(s) exceeded the {MAX_TIME_LIMIT_SECONDS}s "
            "platform maximum and were capped"
        )
    return notes
