"""Comparing a module's materials against the session plan that asks for them.

This is where the three skills meet. A session row names the file that serves
it, so the plan is a manifest: `program` writes the row, and this checks that
the half belonging to teaching material actually exists.

The plan is read **by column name, tolerating any superset**, and its schema is
deliberately not enforced here — that is `program verify`'s job. Each skill
checks only what it owns, so there is no shared constant to drift and no second
copy of the rulebook.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.common.findings import Report

from .grammar import OBJECTIVE_CODE

MATERIALS_COLUMN = "Training Materials / Logistics & General Notes"
OBJECTIVES_COLUMN = "Learning Objectives"
CONTENT_COLUMN = "Content"

#: A materials cell is prose that names files: "dbf_assignment_01.md and rubric".
FILENAME = re.compile(r"\b[\w.-]+\.(?:md|csv|json|xlsx|pdf)\b")

#: Which skill owns a named file, by the shape of its name.
MATERIAL_KINDS = (
    re.compile(r"_lab_\d+\.md$"),
    re.compile(r"_lecture_\d+\.md$"),
    re.compile(r"^\d{2}[a-z]?_.+\.md$"),
)
ASSESSMENT_KINDS = (
    re.compile(r"_quiz_"),
    re.compile(r"_assignment_"),
    re.compile(r"_exam_"),
    re.compile(r"_rubric"),
)


@dataclass(frozen=True)
class Demand:
    filename: str
    session: str
    objectives: tuple[str, ...]
    content: str


def owns(filename: str) -> bool:
    """Is this a file this skill is responsible for producing?"""
    if any(pattern.search(filename) for pattern in ASSESSMENT_KINDS):
        return False
    return any(pattern.search(filename) for pattern in MATERIAL_KINDS)


def read_demands(path: Path) -> list[Demand]:
    if not path.is_file():
        raise UsageError(f"session plan not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or MATERIALS_COLUMN not in rows[0]:
        raise UsageError(
            f"{path.name} has no {MATERIALS_COLUMN!r} column",
            hint="this reads a topic's ScheduleDetail CSV",
        )
    demands = []
    for row in rows:
        cell = row.get(MATERIALS_COLUMN) or ""
        for filename in FILENAME.findall(cell):
            demands.append(
                Demand(
                    filename=filename,
                    session=(row.get("Session") or "").strip(),
                    objectives=tuple(OBJECTIVE_CODE.findall(row.get(OBJECTIVES_COLUMN) or "")),
                    content=(row.get(CONTENT_COLUMN) or "").strip(),
                )
            )
    return demands


def check(
    demands: list[Demand],
    directory: Path,
    report: Report,
    *,
    defined_objectives: set[str] | None = None,
) -> dict:
    """Both directions: what the plan asks for, and what the folder holds."""
    present = {path.name for path in directory.glob("*.md")} if directory.is_dir() else set()
    wanted = {demand.filename for demand in demands if owns(demand.filename)}
    others = {demand.filename for demand in demands if not owns(demand.filename)}

    where = directory.name or str(directory)
    by_name: dict[str, Demand] = {}
    for demand in demands:
        by_name.setdefault(demand.filename, demand)

    missing = sorted(wanted - present)
    for filename in missing:
        demand = by_name[filename]
        report.error(
            "MAT-C01",
            where,
            f"session {demand.session or '?'} names {filename}, which does not exist"
            + (f" — {demand.content[:60]}" if demand.content else ""),
        )

    unused = sorted(present - wanted)
    for filename in unused:
        report.warn("MAT-C02", where, f"{filename} is not used by any session")

    if defined_objectives is not None:
        for demand in demands:
            for code in demand.objectives:
                if code not in defined_objectives:
                    report.warn(
                        "MAT-C04",
                        where,
                        f"session {demand.session or '?'} cites {code}, "
                        "which the syllabus does not define",
                    )

    return {
        "named by the plan": len(wanted),
        "present": len(wanted & present),
        "missing": len(missing),
        "unused": len(unused),
        "owned by another skill": len(others),
    }


def check_objectives(demands: list[Demand], directory: Path, report: Report) -> None:
    """A material should serve the objectives its session claims."""
    from . import notes

    by_name = {demand.filename: demand for demand in demands}
    for filename, demand in sorted(by_name.items()):
        path = directory / filename
        if not owns(filename) or not path.is_file() or not demand.objectives:
            continue
        cited = set(OBJECTIVE_CODE.findall(notes.parse(path).text))
        if not cited:
            continue
        stray = sorted(set(demand.objectives) - cited)
        if stray:
            report.warn(
                "MAT-C03",
                filename,
                f"session {demand.session or '?'} serves {', '.join(stray)}, "
                "which this material never mentions",
            )


__all__ = [
    "CONTENT_COLUMN",
    "MATERIALS_COLUMN",
    "OBJECTIVES_COLUMN",
    "Demand",
    "check",
    "check_objectives",
    "owns",
    "read_demands",
]
