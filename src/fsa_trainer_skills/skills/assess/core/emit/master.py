"""Reading the master question CSV — the single source every emitter derives from.

Nothing downstream is hand-authored. The model writes exactly one artifact, the
master, and the Blooket CSV and Coderbyte JSON are both generated from it. That
is what stops them drifting apart, which was the most common defect when they
were written separately.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from fsa_trainer_skills.errors import UsageError

from ..verify.common import MASTER_COLUMNS

#: How many `Answer N` columns the master may carry. The standard header has 4;
#: extended masters may add up to two more.
MAX_OPTIONS = 6


@dataclass(frozen=True)
class Question:
    number: int
    unit: str
    bloom: str
    difficulty: str
    text: str
    options: list[str]
    correct: list[int]  # 1-based
    time_limit: str
    note: str

    @property
    def is_multi(self) -> bool:
        return len(self.correct) > 1

    def option(self, one_based: int) -> str:
        return self.options[one_based - 1]

    @property
    def correct_field(self) -> str:
        """The master's `Correct Answer(s)` cell, e.g. `2` or `1,3`."""
        return ",".join(str(n) for n in self.correct)


def _parse_correct(value: str, number: int, option_count: int) -> list[int]:
    answers: list[int] = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            parsed = int(raw)
        except ValueError:
            raise UsageError(f"question {number}: correct answer {raw!r} is not a number") from None
        if not 1 <= parsed <= option_count:
            raise UsageError(
                f"question {number}: correct answer {parsed} is outside 1-{option_count}"
            )
        answers.append(parsed)
    if not answers:
        raise UsageError(f"question {number}: no correct answer given")
    return answers


def read(path: Path) -> list[Question]:
    if not path.is_file():
        raise UsageError(f"master CSV not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if fieldnames[: len(MASTER_COLUMNS)] != MASTER_COLUMNS:
            raise UsageError(
                "master CSV header does not match the expected columns",
                hint=(
                    "expected: " + ",".join(MASTER_COLUMNS) + "\n"
                    "       found:    " + ",".join(fieldnames)
                ),
            )
        extra_option_columns = [
            name for name in fieldnames if name.startswith("Answer ") and name not in MASTER_COLUMNS
        ]
        rows = list(reader)

    questions: list[Question] = []
    for index, row in enumerate(rows, start=1):
        number = int(row["No"].strip() or index)
        options = [row[f"Answer {n}"].strip() for n in range(1, 5)]
        for name in extra_option_columns:
            value = (row.get(name) or "").strip()
            if value:
                options.append(value)
        options = [option for option in options if option]
        if len(options) < 2:
            raise UsageError(f"question {number}: needs at least two answer options")

        questions.append(
            Question(
                number=number,
                unit=row["Unit/Lecture"].strip(),
                bloom=row["Bloom Level"].strip(),
                difficulty=row["Difficulty"].strip(),
                text=row["Question"].strip(),
                options=options,
                correct=_parse_correct(row["Correct Answer(s)"], number, len(options)),
                time_limit=row["Time Limit (sec)"].strip(),
                note=(row.get("Note") or "").strip(),
            )
        )

    if not questions:
        raise UsageError(f"master CSV has no questions: {path}")
    return questions
