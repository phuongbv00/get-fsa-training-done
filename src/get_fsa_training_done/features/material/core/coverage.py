"""Comparing a module's materials against the session plan that asks for them.

This is where the three features meet. A session row names the file that
serves it, so the plan is a manifest: `program` writes the row, and this checks
that the half belonging to teaching material actually exists.

The plan is read **by column name, tolerating any superset**, and its schema is
deliberately not enforced here — that is `program verify`'s job. Each feature
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

from .grammar import (
    LAB_FILENAME,
    NOTE_FILENAME,
    OBJECTIVE_CODE,
    WORKSHEET_FILENAME,
    is_translation,
    legacy,
)

MATERIALS_COLUMN = "Training Materials / Logistics & General Notes"
OBJECTIVES_COLUMN = "Learning Objectives"
CONTENT_COLUMN = "Content"

#: A materials cell is prose that names files: "dbf_assignment_01.md and rubric".
FILENAME = re.compile(r"\b[\w.-]+\.(?:html|md|csv|json|xlsx|pdf)\b")

#: Which feature owns a named file, by the shape of its name.
MATERIAL_KINDS = (
    re.compile(r"_lab_\d+(?:_vn)?\.html$"),
    WORKSHEET_FILENAME,
    NOTE_FILENAME,
    re.compile(r"_lecture_\d+\.html$"),
    re.compile(r"^\d{2}[a-z]?_.+\.html$"),
)
#: Material named with a `.md` extension: a plan written before material became
#: HTML. Still this feature's, and reported missing with the name it should have.
STALE_MARKDOWN = (
    re.compile(r"_lab_\d+(?:_vn)?\.md$"),
    re.compile(r"_lab_\d+_worksheet(?:_vn)?\.md$"),
    re.compile(r"_lecture_note(?:_vn)?\.md$"),
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
    """Is this a file this feature is responsible for producing?"""
    if any(pattern.search(filename) for pattern in ASSESSMENT_KINDS):
        return False
    return any(pattern.search(filename) for pattern in (*MATERIAL_KINDS, *STALE_MARKDOWN))


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
    present = {path.name for path in directory.glob("*.html")} if directory.is_dir() else set()
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
            + _rename_hint(filename)
            + (f" — {demand.content[:60]}" if demand.content else ""),
        )

    unused = sorted(
        filename for filename in present - wanted if not _in_use(filename, present, wanted)
    )
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
        "owned by another feature": len(others),
    }


def _in_use(filename: str, present: set[str], wanted: set[str]) -> bool:
    """Is a file no session names still in use through another one?

    A translation is, whenever its original is; a worksheet serves its lab, and
    is in use whenever the lab beside it is.
    """
    if filename in wanted:
        return True
    if WORKSHEET_FILENAME.match(filename):
        lab = _lab_of(filename)
        return lab in present and bool(LAB_FILENAME.match(lab))
    if is_translation(filename):
        original = _original_of(filename)
        return original in present and _in_use(original, present, wanted)
    return False


def _original_of(translation: str) -> str:
    """`dbf_lecture_note_vn.html` translates `dbf_lecture_note.html`."""
    return re.sub(r"_vn((?:\.deck)?\.html)$", r"\1", translation)


def _rename_hint(filename: str) -> str:
    """What the plan should name instead, when a name has an older shape."""
    # A `.md` name is checked as the `.html` it would become: `02_Querying.md`
    # is an old per-session note, not something to rename to `02_Querying.html`.
    as_html = filename[:-3] + ".html" if filename.endswith(".md") else filename
    advice = legacy(filename) or legacy(as_html)
    if advice is not None:
        return f"; {advice}, and the plan should name <subject>_lecture_note.html"
    if filename.endswith(".md"):
        return f"; material is HTML, so the plan should name {filename[:-3]}.html"
    return ""


def _lab_of(worksheet: str) -> str:
    """`dbf_lab_01_worksheet_vn.html` serves `dbf_lab_01.html`."""
    return re.sub(r"_worksheet(_vn)?\.html$", ".html", worksheet)


def check_objectives(demands: list[Demand], directory: Path, report: Report) -> None:
    """A material should serve the objectives of every session that names it.

    The lecture note is named by each lecture row of the module, so what it must
    mention is the union of their objectives, not the last row's.
    """
    from . import dom

    by_name: dict[str, list[Demand]] = {}
    for demand in demands:
        by_name.setdefault(demand.filename, []).append(demand)
    for filename, named in sorted(by_name.items()):
        path = directory / filename
        if not owns(filename) or not path.is_file():
            continue
        cited = set(OBJECTIVE_CODE.findall(dom.parse(path).source))
        if not cited:
            continue
        for demand in named:
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
