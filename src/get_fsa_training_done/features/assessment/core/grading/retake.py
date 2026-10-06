"""Merge a first-attempt grade CSV with a retake's into one result per trainee.

Both inputs are `grade aggregate` output. The policy is the programme's, so
every part of it is a flag with the usual default:

- `cap` (default 6): a retake can earn at most this total. Its task scores are
  left as graded; only the total is capped, and the comment says why.
- `keep` (default `higher`): keep whichever attempt has the higher effective
  total — the retake's after its cap — or always the retake (`retake`).
- `void`: trainees whose retake was cancelled, for instance for cheating.
  Their first attempt stands, whatever the retake scored; one who has no first
  attempt keeps a row with no scores and no total, so the gap stays visible.

The attempt kept supplies the task scores and the comment, so feedback always
describes the work the total came from. The inputs are never modified.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from .aggregate import fmt
from .roster import Roster

ID, NAME, COMMENT, TOTAL = "Std ID", "Name", "Comment", "Total"
KEEP_POLICIES = ("higher", "retake")
DEFAULT_CAP = 6.0
DEFAULT_CAP_NOTE = "Retake: the total is capped at {cap}."


@dataclass
class Sheet:
    headers: list[str]
    rows: dict[str, dict[str, str]]
    order: list[str]

    @property
    def tasks(self) -> list[str]:
        return [h for h in self.headers if h not in (ID, NAME, COMMENT, TOTAL)]


@dataclass
class Merge:
    headers: list[str]
    rows: list[list[str]]
    from_retake: list[str] = field(default_factory=list)
    capped: list[str] = field(default_factory=list)
    voided: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def read(path: Path) -> Sheet:
    if not path.is_file():
        raise UsageError(f"grade CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        missing = [column for column in (ID, TOTAL) if column not in headers]
        if missing:
            raise UsageError(
                f"{path} is not a `grade aggregate` CSV (missing {', '.join(missing)})"
            )
        rows: dict[str, dict[str, str]] = {}
        order: list[str] = []
        for row in reader:
            std_id = (row.get(ID) or "").strip()
            if std_id:
                rows[std_id.lower()] = row
                order.append(std_id)
    return Sheet(headers=headers, rows=rows, order=order)


def _number(value: str | None) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def merge(
    first: Sheet,
    retake: Sheet,
    *,
    cap: float = DEFAULT_CAP,
    keep: str = "higher",
    void: list[str] | None = None,
    cap_note: str = DEFAULT_CAP_NOTE,
    roster: Roster | None = None,
) -> Merge:
    if keep not in KEEP_POLICIES:
        raise UsageError(f"--keep must be one of {', '.join(KEEP_POLICIES)}")
    voided = {std_id.strip().lower() for std_id in (void or []) if std_id.strip()}

    # Two different papers rarely share a task list. Keep the columns positional
    # and drop the weights from their headers rather than label one paper's
    # scores with the other's weights.
    same_tasks = first.tasks == retake.tasks
    width = max(len(first.tasks), len(retake.tasks))
    task_headers = first.tasks if same_tasks else [f"T{i + 1}" for i in range(width)]
    result = Merge(headers=[ID, NAME, COMMENT, *task_headers, TOTAL], rows=[])
    if not same_tasks:
        result.notes.append(
            "the two papers have different task lists; T columns hold each kept "
            "attempt's own tasks in order, without weights"
        )

    order = roster.order() if roster else list(first.order)
    seen = {std_id.lower() for std_id in order}
    order += [std_id for std_id in first.order + retake.order if std_id.lower() not in seen]
    seen = set()

    for std_id in order:
        key = std_id.lower()
        if key in seen:
            continue
        seen.add(key)
        original, second = first.rows.get(key), retake.rows.get(key)
        if original is None and second is None:
            continue

        kept, sheet, total, note = original, first, _number((original or {}).get(TOTAL)), ""
        if second is not None:
            raw = _number(second.get(TOTAL))
            effective = None if raw is None else min(raw, cap)
            if key in voided:
                result.voided.append(std_id)
            elif (
                original is None
                or keep == "retake"
                or (effective is not None and (total is None or effective > total))
            ):
                kept, sheet, total = second, retake, effective
                result.from_retake.append(std_id)
                if raw is not None and raw > cap:
                    note = cap_note.format(cap=fmt(cap))
                    result.capped.append(std_id)

        roster_name = roster.get(std_id).name if roster and roster.get(std_id) else ""
        if kept is None:
            # A voided retake and no first attempt: nothing stands.
            name = roster_name or (second or {}).get(NAME, "")
            result.rows.append([std_id, name, "", *([""] * len(task_headers)), ""])
            continue
        name = kept.get(NAME, "") or roster_name
        comment = " | ".join(part for part in ((kept.get(COMMENT) or "").strip(), note) if part)
        scores = [kept.get(task, "") for task in sheet.tasks]
        scores += [""] * (len(task_headers) - len(scores))
        result.rows.append([kept.get(ID, std_id), name, comment, *scores, fmt(total)])

    return result


def write(merged: Merge, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(merged.headers)
        writer.writerows(merged.rows)
