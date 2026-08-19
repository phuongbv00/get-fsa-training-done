"""The class roster, and matching a submission filename back to a trainee.

One roster reader, one definition of "dropped", one id-matching rule. The
original scripts each had their own: three of them treated `inactive` as
dropped and the fourth did not, so a trainee marked `inactive` was skipped at
preprocess, batch, and quiz time but silently reappeared in the aggregated
grades. Centralising it is the fix.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from fsa_trainer_skills.errors import UsageError

#: Every spelling of "no longer in this class" that appears in real rosters.
DROPPED_STATUSES = {"drop", "dropped", "inactive", "withdrawn"}

ID_COLUMN = "ID"
NAME_COLUMN = "Name"
STATUS_COLUMN = "Status"


@dataclass(frozen=True)
class Trainee:
    std_id: str
    name: str
    status: str

    @property
    def dropped(self) -> bool:
        return self.status.strip().lower() in DROPPED_STATUSES


@dataclass
class Roster:
    path: Path
    trainees: list[Trainee]

    def __post_init__(self) -> None:
        self._by_lower = {trainee.std_id.lower(): trainee for trainee in self.trainees}

    @property
    def active(self) -> list[Trainee]:
        return [trainee for trainee in self.trainees if not trainee.dropped]

    @property
    def dropped_ids(self) -> set[str]:
        return {t.std_id.lower() for t in self.trainees if t.dropped}

    def get(self, std_id: str) -> Trainee | None:
        return self._by_lower.get(std_id.strip().lower())

    def is_dropped(self, std_id: str) -> bool:
        trainee = self.get(std_id)
        return bool(trainee and trainee.dropped)

    def order(self) -> list[str]:
        return [trainee.std_id for trainee in self.trainees]


def load(path: Path) -> Roster:
    if not path.is_file():
        raise UsageError(f"roster not found: {path}")

    trainees: list[Trainee] = []
    # utf-8-sig: real rosters are exported from Excel and carry a BOM.
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if ID_COLUMN not in fields:
            raise UsageError(
                f"roster {path} has no {ID_COLUMN!r} column",
                hint=f"found: {', '.join(fields)}",
            )
        for row in reader:
            std_id = (row.get(ID_COLUMN) or "").strip()
            if not std_id:
                continue
            trainees.append(
                Trainee(
                    std_id=std_id,
                    name=(row.get(NAME_COLUMN) or "").strip(),
                    status=(row.get(STATUS_COLUMN) or "").strip(),
                )
            )

    if not trainees:
        raise UsageError(f"roster {path} has no trainees")
    return Roster(path=path, trainees=trainees)


def tokens(stem: str) -> list[str]:
    return [token for token in re.split(r"[^A-Za-z0-9]+", stem) if token]


def match_std_id(stem: str, roster: Roster) -> tuple[str, bool]:
    """Resolve a filename stem to a canonical roster id.

    Three tiers, most reliable first: an exact token match, then the longest
    roster id appearing inside the collapsed stem, then the last token as a
    raw fallback flagged unknown.
    """
    parts = tokens(stem)
    for token in parts:
        trainee = roster.get(token)
        if trainee:
            return trainee.std_id, True

    collapsed = re.sub(r"[^A-Za-z0-9]+", "", stem).lower()
    best: tuple[str, str] | None = None
    for trainee in roster.trainees:
        lowered = trainee.std_id.lower()
        if lowered in collapsed and (best is None or len(lowered) > len(best[0])):
            best = (lowered, trainee.std_id)
    if best:
        return best[1], True

    return (parts[-1] if parts else stem), False


def folder_name(subject: str, submission_type: str, std_id: str) -> str:
    return f"{subject.upper()}_{submission_type.upper()}_{std_id}"


def std_id_from_folder(name: str, subject: str, submission_type: str) -> str:
    """Recover the trainee id from a canonical folder name.

    Deliberately strips the known `<SUBJECT>_<TYPE>_` prefix instead of taking
    the last underscore-separated token. The original scripts all used
    `name.split("_")[-1]`, which silently truncates any roster id that itself
    contains an underscore — the id would then match nothing and the
    submission would vanish from the aggregated grades without a word.
    """
    prefix = f"{subject.upper()}_{submission_type.upper()}_"
    if name.upper().startswith(prefix):
        return name[len(prefix) :]
    return name.rsplit("_", 1)[-1]
