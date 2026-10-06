"""Roll per-submission score sheets up into one grade CSV.

Output columns:

    Std ID, Name, Comment, T1 (weight%), ..., TN (weight%), Total

`T1..TN` are raw 0-10 task scores in rubric order and `Total` is the weighted
score, `sum(score * weight) / 100`. Caps, deductions, and bonuses are folded
into the task score they belong to, so there is no separate adjustment step.

Older sheets that still carry `bonus` / `adjustments` / `deductions` keep
aggregating to the total they always did. Their *reasons* are rendered into the
Comment column so no feedback is lost, but never their signed amounts — score
arithmetic is instructor-only and must not reach a learner.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from .roster import Roster


@dataclass
class Aggregation:
    headers: list[str]
    rows: list[list[str]]
    legend: str
    task_order: list[str] = field(default_factory=list)
    skipped_dropped: list[str] = field(default_factory=list)


def fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return str(int(value))
        return f"{float(value):.2f}".rstrip("0").rstrip(".")
    return str(value)


def as_number(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def weighted_total(data: dict) -> float | None:
    weighted = 0.0
    saw_task = False
    for task in data.get("tasks", []):
        score = as_number(task.get("score"))
        weight = as_number(task.get("weight"))
        if weight is None:
            weight = as_number(task.get("weighted_number"))
        if score is None or weight is None:
            return None
        weighted += score * weight / 100.0
        saw_task = True
    return weighted if saw_task else None


def legacy_bonus(data: dict) -> float | None:
    """The signed adjustment older sheets recorded, or None for current ones."""
    explicit = as_number(data.get("bonus"))
    if explicit is not None:
        return explicit
    if data.get("adjustments") is not None:
        return sum(as_number(item.get("amount")) or 0.0 for item in data["adjustments"])
    if data.get("deductions") is not None:
        # The oldest sheets recorded deductions as positive amounts to subtract.
        return -sum(as_number(item.get("amount")) or 0.0 for item in data["deductions"])
    return None


def final_total(data: dict, weighted: float | None) -> float | None:
    bonus = legacy_bonus(data)
    if bonus is not None and weighted is not None:
        return max(0.0, weighted + bonus)
    if weighted is not None:
        return weighted
    return as_number(data.get("total"))


def load_order(path: Path | None) -> list[str]:
    if not path:
        return []
    return [
        line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()
    ]


def aggregate(
    *,
    scores_dir: Path,
    roster: Roster | None,
    order_path: Path | None = None,
    include_dropped: list[str] | None = None,
) -> Aggregation:
    files = sorted(scores_dir.glob("*.json"))
    if not files:
        raise UsageError(f"no score JSON files found in {scores_dir}")

    include = {std_id.strip().lower() for std_id in (include_dropped or []) if std_id.strip()}
    dropped = roster.dropped_ids if roster else set()
    names = {trainee.std_id.lower(): trainee.name for trainee in roster.trainees} if roster else {}

    explicit_order = load_order(order_path)
    if explicit_order:
        row_order = explicit_order
    elif roster:
        active = [trainee.std_id for trainee in roster.active]
        extra = [
            trainee.std_id
            for trainee in roster.trainees
            if trainee.dropped and trainee.std_id.lower() in include
        ]
        row_order = active + extra
    else:
        row_order = []
    rank_of = {std_id.lower(): index for index, std_id in enumerate(row_order)}

    records: list[tuple[Path, dict]] = []
    task_order: list[str] = []
    task_meta: dict[str, dict] = {}
    skipped: list[str] = []

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise UsageError(f"invalid JSON in {path}: {exc}") from None

        std_id = (data.get("std_id") or path.stem).strip()
        if std_id.lower() in dropped and std_id.lower() not in include:
            skipped.append(std_id)
            continue

        for task in data.get("tasks", []):
            task_id = task.get("id")
            if not task_id or task_id in task_meta:
                continue
            task_order.append(task_id)
            task_meta[task_id] = {
                "name": task.get("name", ""),
                "max": task.get("max", task.get("max_score", "")),
                "weight": task.get("weight", task.get("weighted_number", "")),
            }
        records.append((path, data))

    headers = (
        ["Std ID", "Name", "Comment"]
        + [
            f"T{index + 1} ({fmt(task_meta[task_id].get('weight'))}%)"
            if task_meta[task_id].get("weight") not in (None, "")
            else f"T{index + 1}"
            for index, task_id in enumerate(task_order)
        ]
        + ["Total"]
    )

    ranked: list[tuple[int, int, list[str]]] = []
    for position, (path, data) in enumerate(records):
        std_id = data.get("std_id") or path.stem
        name = data.get("name") or names.get(std_id.lower(), "")
        by_id = {task.get("id"): task for task in data.get("tasks", [])}

        cells: list[str] = []
        comments: list[str] = []
        for task_id in task_order:
            task = by_id.get(task_id)
            if task is None:
                cells.append("")
                continue
            cells.append(fmt(task.get("score", "")))
            comment = (task.get("comment") or "").strip()
            if comment:
                comments.append(f"{task_id}: {comment}")

        for adjustment in data.get("adjustments") or data.get("deductions") or []:
            reason = (adjustment.get("reason") or "").strip()
            if reason:
                comments.append(reason)
        legacy_comment = (data.get("comment") or "").strip()
        if legacy_comment:
            comments.append(legacy_comment)

        total = final_total(data, weighted_total(data))
        row = [std_id, name, " | ".join(comments), *cells, fmt(total)]
        rank = rank_of.get(std_id.lower(), len(rank_of) + position)
        ranked.append((rank, position, row))

    ranked.sort(key=lambda item: (item[0], item[1]))
    rows = [row for _, _, row in ranked]

    return Aggregation(
        headers=headers,
        rows=rows,
        legend=_legend(task_order, task_meta),
        task_order=task_order,
        skipped_dropped=skipped,
    )


def _legend(task_order: list[str], task_meta: dict[str, dict]) -> str:
    lines = ["task legend"]
    for index, task_id in enumerate(task_order):
        meta = task_meta.get(task_id, {})
        details = []
        if meta.get("max") not in (None, ""):
            details.append(f"max {fmt(meta.get('max'))}")
        if meta.get("weight") not in (None, ""):
            details.append(f"weight {fmt(meta.get('weight'))}%")
        suffix = f" ({', '.join(details)})" if details else ""
        lines.append(f"  T{index + 1} = {task_id}  {meta.get('name', '')}{suffix}".rstrip())
    return "\n".join(lines)


def write_rows(path: Path, rows: list[list[str]]) -> None:
    """Every CSV the grading pipeline writes: UTF-8 with a BOM, so Excel opens
    the Vietnamese names correctly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        csv.writer(handle).writerows(rows)


def write(aggregation: Aggregation, out: Path) -> Path:
    write_rows(out, [aggregation.headers, *aggregation.rows])

    legend_path = out.with_suffix(".legend.txt")
    legend_path.write_text(
        aggregation.legend.replace("task legend", f"{out.name} — task legend", 1) + "\n",
        encoding="utf-8",
    )
    return legend_path
