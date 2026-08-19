"""Partition preprocessed submissions into even batches for parallel grading.

Grading judgement belongs to the model, not to a script. This only decides who
goes in which batch, and by default skips anyone who already has a score sheet
so a re-run picks up exactly the leftovers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fsa_trainer_skills.errors import UsageError

from .roster import Roster, std_id_from_folder

SKIP_DIRECTORIES = {"_scores", "_plagiarism", "_ai_cheat"}


@dataclass
class Plan:
    preprocessed: str
    scores: str
    total: int
    pending: int
    already_scored: int
    dropped: int
    dropped_std_ids: list[str]
    batches: list[dict]

    def to_dict(self) -> dict:
        return {
            "preprocessed": self.preprocessed,
            "scores": self.scores,
            "total": self.total,
            "pending": self.pending,
            "already_scored": self.already_scored,
            "dropped": self.dropped,
            "dropped_std_ids": self.dropped_std_ids,
            "batches": self.batches,
        }


def plan(
    *,
    preprocessed: Path,
    scores: Path,
    roster: Roster | None,
    subject: str,
    submission_type: str,
    batch_count: int = 4,
    include_scored: bool = False,
) -> Plan:
    if not preprocessed.is_dir():
        raise UsageError(f"not a directory: {preprocessed}")

    dropped_ids = roster.dropped_ids if roster else set()

    folders: list[tuple[str, str]] = []
    dropped: list[tuple[str, str]] = []
    for entry in sorted(preprocessed.iterdir()):
        if not entry.is_dir() or entry.name in SKIP_DIRECTORIES or entry.name.startswith("_"):
            continue
        std_id = std_id_from_folder(entry.name, subject, submission_type)
        if std_id.lower() in dropped_ids:
            dropped.append((entry.name, std_id))
            continue
        folders.append((entry.name, std_id))

    scored = {path.stem for path in scores.glob("*.json")} if scores.is_dir() else set()
    pending = folders if include_scored else [item for item in folders if item[1] not in scored]

    count = max(1, batch_count)
    buckets: list[list[tuple[str, str]]] = [[] for _ in range(count)]
    for index, item in enumerate(pending):
        # Round-robin rather than contiguous slices, so the batches stay even
        # when the count does not divide the total.
        buckets[index % count].append(item)

    return Plan(
        preprocessed=str(preprocessed),
        scores=str(scores),
        total=len(folders),
        pending=len(pending),
        already_scored=len(folders) - len(pending),
        dropped=len(dropped),
        dropped_std_ids=[std_id for _, std_id in dropped],
        batches=[
            {
                "index": index + 1,
                "folders": [name for name, _ in bucket],
                "std_ids": [std_id for _, std_id in bucket],
            }
            for index, bucket in enumerate(buckets)
            if bucket
        ],
    )
