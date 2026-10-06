"""Put several quizzes' score CSVs side by side, one row per trainee.

Each input is `grade quiz` output (`Std ID, score`, on a 10-point scale). The
output follows the roster — active trainees, in roster order — so it can be
pasted next to the class list: `No, ID, Name, <one column per quiz>`. A quiz a
trainee did not sit is left blank, not zero: whether a missing quiz counts as
zero is the programme's call, and a blank keeps that decision visible.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from .aggregate import write_rows
from .roster import Roster


@dataclass
class Merged:
    headers: list[str]
    rows: list[list[str]]
    #: Ids in an input that are not active on the roster, by quiz label.
    unknown: dict[str, list[str]] = field(default_factory=dict)


def parse_inputs(values: list[str]) -> list[tuple[str, Path]]:
    inputs: list[tuple[str, Path]] = []
    for value in values:
        label, sep, path = value.partition("=")
        if not sep or not label.strip() or not path.strip():
            raise UsageError(f"--quiz takes LABEL=CSV, got {value!r}")
        inputs.append((label.strip(), Path(path.strip()).expanduser()))
    labels = [label for label, _ in inputs]
    if len(set(labels)) != len(labels):
        raise UsageError("each --quiz needs its own label")
    return inputs


def read_scores(path: Path) -> dict[str, tuple[str, str]]:
    """Each id, matched case-insensitively, to the id as written and its score."""
    if not path.is_file():
        raise UsageError(f"quiz score CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not {"Std ID", "score"} <= set(reader.fieldnames or []):
            raise UsageError(f"{path} is not `grade quiz` output (Std ID, score)")
        return {
            row["Std ID"].strip().lower(): (row["Std ID"].strip(), row["score"].strip())
            for row in reader
            if row.get("Std ID", "").strip()
        }


def merge(inputs: list[tuple[str, Path]], roster: Roster) -> Merged:
    if not inputs:
        raise UsageError("give at least one --quiz LABEL=CSV")
    scores = [(label, read_scores(path)) for label, path in inputs]
    active = roster.active
    known = {trainee.std_id.lower() for trainee in active}
    merged = Merged(headers=["No", "ID", "Name", *(label for label, _ in scores)], rows=[])
    for number, trainee in enumerate(active, start=1):
        key = trainee.std_id.lower()
        merged.rows.append(
            [
                str(number),
                trainee.std_id,
                trainee.name,
                *(table.get(key, ("", ""))[1] for _, table in scores),
            ]
        )
    for label, table in scores:
        stray = sorted(written for key, (written, _) in table.items() if key not in known)
        if stray:
            merged.unknown[label] = stray
    return merged


def write(merged: Merged, out: Path) -> None:
    write_rows(out, [merged.headers, *merged.rows])
