"""One module's quizzes: a results CSV in, one score per trainee per quiz out.

A module's quiz results arrive from several places — a platform's report
workbook, a pasted Blooket leaderboard, a screenshot the agent reads — so they
are first written into one results CSV, a row per player per attempt:

    quiz, part, nickname, correct, incorrect, answered, unattempted

`quiz` is the column label the score will go under ("JCF 01"); `part` tells a
live game from its homework run. `answered` and `unattempted` are optional:
a leaderboard or a screenshot has neither, and is scored out of the quiz's
question count, which `questions` supplies. Both cases reduce to the rule in
`quiz_scores`:

    expected_total = max(answered, correct + incorrect) + unattempted
    score = ceil(correct / expected_total * 10, 1 decimal)

with a missing `unattempted` taken as whatever the quiz holds beyond what the
player answered. A trainee's best attempt at a quiz is kept.

The score CSV follows the roster — active trainees, in roster order —
`No, ID, Name, <one column per quiz>`, quizzes in the order the results CSV
first names them. A quiz a trainee did not sit stays blank: the CSV records
what happened, and whether a blank counts as zero is decided where the marks
are uploaded.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from . import quiz_scores
from .aggregate import write_rows
from .roster import Roster

RESULT_HEADERS = ["quiz", "part", "nickname", "correct", "incorrect", "answered", "unattempted"]
REQUIRED = ["quiz", "nickname", "correct", "incorrect"]


@dataclass
class ModuleScores:
    headers: list[str]
    rows: list[list[str]]
    #: Nicknames no roster id or alias matches, by quiz label.
    unmatched: dict[str, list[str]] = field(default_factory=dict)
    #: Roster ids skipped because the trainee dropped, by quiz label.
    dropped: dict[str, list[str]] = field(default_factory=dict)
    #: How many trainees have a score, by quiz label.
    scored: dict[str, int] = field(default_factory=dict)


def _count(value: str, where: str) -> int | None:
    text = (value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        number = int(float(text))
    except ValueError:
        raise UsageError(f"{where}: {value!r} is not a count") from None
    if number < 0:
        raise UsageError(f"{where}: {value!r} is negative")
    return number


def read_results(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise UsageError(f"results CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in REQUIRED if name not in (reader.fieldnames or [])]
        if missing:
            raise UsageError(
                f"results CSV {path} is missing column(s): {', '.join(missing)}",
                hint=f"columns: {', '.join(RESULT_HEADERS)}",
            )
        rows = [row for row in reader if (row.get("nickname") or "").strip()]
    if not rows:
        raise UsageError(f"results CSV {path} has no players")
    return rows


def append_results(path: Path, rows: list[list[str]]) -> None:
    """Add rows (in `RESULT_HEADERS` order), writing the header on a new file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fresh = not path.exists() or path.stat().st_size == 0
    if not fresh:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            header = next(csv.reader(handle), [])
        if header != RESULT_HEADERS:
            raise UsageError(
                f"{path} is not a results CSV this command wrote",
                hint=f"its header should be: {', '.join(RESULT_HEADERS)}",
            )
    with path.open("a", newline="", encoding="utf-8-sig" if fresh else "utf-8") as handle:
        writer = csv.writer(handle)
        if fresh:
            writer.writerow(RESULT_HEADERS)
        writer.writerows(rows)


def from_report(rows: list[list[str]], quiz: str, part: str) -> list[list[str]]:
    """Report or leaderboard rows (`quiz_scores` headers) as results rows."""
    headers = rows[0]
    at = {
        name: quiz_scores._column_index(headers, columns)
        for name, columns in (
            ("nickname", quiz_scores.NICKNAME_COLUMN),
            ("answered", quiz_scores.ANSWERED_COLUMN),
            ("correct", quiz_scores.CORRECT_COLUMN),
            ("incorrect", quiz_scores.INCORRECT_COLUMN),
            ("unattempted", quiz_scores.UNATTEMPTED_COLUMN),
        )
    }

    def cell(row: list[str], name: str) -> str:
        index = at[name]
        return row[index].strip() if index < len(row) else ""

    return [
        [
            quiz,
            part,
            cell(row, "nickname"),
            cell(row, "correct"),
            cell(row, "incorrect"),
            cell(row, "answered"),
            cell(row, "unattempted"),
        ]
        for row in rows[1:]
        if cell(row, "nickname")
    ]


def parse_questions(default: int | None, values: list[str]) -> dict[str, int]:
    """`--questions-for LABEL=N` overrides; the default is kept under ''."""
    counts: dict[str, int] = {}
    if default is not None:
        counts[""] = default
    for value in values:
        label, sep, number = value.partition("=")
        try:
            counts[label.strip()] = int(number)
        except ValueError:
            sep = ""
        if not sep or not label.strip() or counts.get(label.strip(), 0) < 1:
            raise UsageError(f"--questions-for takes LABEL=N with N >= 1, got {value!r}")
    return counts


def score(
    results: list[dict[str, str]],
    roster: Roster,
    questions: dict[str, int],
    aliases: dict[str, str] | None = None,
) -> ModuleScores:
    by_quiz: dict[str, list[list[str]]] = {}
    for line, row in enumerate(results, start=2):
        quiz = (row.get("quiz") or "").strip()
        if not quiz:
            raise UsageError(f"results CSV line {line} has no quiz label")
        where = f"results CSV line {line} ({row['nickname'].strip()})"
        correct = _count(row.get("correct", ""), where) or 0
        incorrect = _count(row.get("incorrect", ""), where) or 0
        answered = _count(row.get("answered", ""), where)
        unattempted = _count(row.get("unattempted", ""), where)
        seen = max(answered or 0, correct + incorrect)
        if unattempted is None:
            total = questions.get(quiz, questions.get(""))
            if total is None:
                raise UsageError(
                    f"{where} has no unattempted count, so {quiz!r} needs its question count",
                    hint="pass --questions N, or --questions-for 'LABEL=N' per quiz",
                )
            unattempted = max(0, total - seen)
        by_quiz.setdefault(quiz, []).append(
            [row["nickname"].strip(), str(seen), str(correct), str(incorrect), str(unattempted)]
        )

    module = ModuleScores(headers=["No", "ID", "Name", *by_quiz], rows=[])
    tables: list[dict[str, str]] = []
    for quiz, rows in by_quiz.items():
        result = quiz_scores.score([list(quiz_scores.LEADERBOARD_HEADERS), *rows], roster, aliases)
        tables.append({std_id.lower(): value for std_id, value in result.rows[1:]})
        module.scored[quiz] = result.scored
        if result.unmatched:
            module.unmatched[quiz] = result.unmatched
        if result.dropped:
            module.dropped[quiz] = result.dropped

    for number, trainee in enumerate(roster.active, start=1):
        key = trainee.std_id.lower()
        module.rows.append(
            [str(number), trainee.std_id, trainee.name, *(table.get(key, "") for table in tables)]
        )
    return module


def write(module: ModuleScores, out: Path) -> None:
    write_rows(out, [module.headers, *module.rows])
