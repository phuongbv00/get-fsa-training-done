"""Capstone-project verification, on top of the shared long-form checks.

A capstone differs from an assignment in four ways that need checking:

* Its tasks are the five programme deliverables D01–D05, so the rubric's task
  list must cover each of them exactly once and in order.
* It is team work, so the rubric needs a task that scores the individual, or
  every member of a team gets the team's mark regardless of contribution.
* It runs in sprints, and a sprint is only a checkpoint if something is due at
  the end of it and something happens when that thing is missing. The spec is
  where the calendar and the gates get pinned down.
* It references a stack and a demo — things the existing hand-written Mock
  Project material mentions but never defines. The spec document is where
  those get pinned down, so its fields are required rather than optional.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .common import CheckResult, read_text
from .long_form import parse_rubric_tasks, section_body

#: The programme's five deliverables. The rubric maps these onto T1..T5, and
#: the spec's sprint table says which sprint each one is due in. The names are
#: here rather than in the workflow prose because `sprint-kit` prints them into
#: the learner handout, and a handout naming D03 something else than the rubric
#: does is a support ticket.
DELIVERABLE_NAMES = {
    "D01": "Project Proposal",
    "D02": "Product Backlog and WBS",
    "D03": "Requirement and Design Documents",
    "D04": "Source Code",
    "D05": "Final Presentation and Demo",
}

DELIVERABLES = tuple(DELIVERABLE_NAMES)

#: Fields the spec must pin down. Each maps to something the current Mock
#: Project files refer to without ever defining. These are marker sets, not
#: exact headings, so a spec that words a section differently still passes; the
#: Vietnamese markers are kept for specs written before the skill standardised
#: on English, and they reject nothing.
REQUIRED_SPEC_FIELDS = {
    "Team size": ("team size", "quy mô nhóm", "số thành viên"),
    "Duration": ("duration", "thời lượng", "thời gian"),
    "Sprints": ("sprint",),
    "Stack": ("stack", "công nghệ", "technology"),
    "Demo": ("demo", "bảo vệ", "presentation", "trình bày"),
    "Contribution": ("contribution", "đóng góp", "individual"),
}

#: The standing sprint gates. G1–G4 repeat unchanged every sprint; G5 is
#: whatever that sprint's row in the spec's table says is due. They carry fixed
#: ids so the rubric's caps can name the gate that triggered them.
CHECKPOINT_GATES = {
    "G1": "backlog freeze",
    "G2": "code tag",
    "G3": "submission folder",
    "G4": "sprint review record",
    "G5": "sprint deliverable",
}

#: Words that mark a rubric task as scoring the individual rather than the team.
CONTRIBUTION_MARKERS = (
    "contribution",
    "individual",
    "per-member",
    "đóng góp",
    "cá nhân",
)

#: A row of the spec's sprint table: number, start, end, deliverables due.
#: Read positionally, so a spec may head the columns in any language.
_SPRINT_ROW = re.compile(
    r"^\|\s*(\d+)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|",
    re.MULTILINE,
)

#: "Sprint 2" anywhere in the brief or rubric. The sprint the deliverable
#: bullets promise has to be one the spec's calendar actually has.
_SPRINT_REFERENCE = re.compile(r"\bsprint\s+(\d+)\b", re.IGNORECASE)

_DELIVERABLE_TOKEN = re.compile(r"\bD\d{2}\b")


@dataclass(frozen=True)
class Sprint:
    number: int
    start: date | None
    end: date | None
    deliverables: tuple[str, ...]


def check_spec(path: Path, result: CheckResult) -> None:
    text = read_text(path, result, label="project spec")
    if not text:
        return
    lowered = text.lower()
    for field, markers in REQUIRED_SPEC_FIELDS.items():
        if not any(marker in lowered for marker in markers):
            result.error(
                f"Project spec does not define {field}; the deliverables reference it "
                "but nothing pins it down"
            )


def _parse_date(value: str, number: int, edge: str, result: CheckResult) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        result.error(
            f"Sprint {number} {edge} date {value.strip()!r} is not ISO 8601 (YYYY-MM-DD); "
            "the checkpoint deadline is the thing every gate is measured against, so it "
            "has to parse"
        )
        return None


def parse_sprints(spec_text: str, result: CheckResult) -> list[Sprint]:
    """Read the sprint calendar out of the spec's `## Sprints` table."""
    body = section_body(spec_text, "## Sprints")
    if not body:
        result.error(
            "Project spec has no '## Sprints' section; every 'due in Sprint N' line "
            "in the brief points at nothing"
        )
        return []

    sprints: list[Sprint] = []
    for match in _SPRINT_ROW.finditer(body):
        number = int(match.group(1))
        sprints.append(
            Sprint(
                number=number,
                start=_parse_date(match.group(2), number, "start", result),
                end=_parse_date(match.group(3), number, "end", result),
                deliverables=tuple(_DELIVERABLE_TOKEN.findall(match.group(4))),
            )
        )

    if not sprints:
        result.error(
            "Spec's Sprints section has no sprint table; it needs one row per sprint "
            "giving the number, the start and end dates, and the deliverables due"
        )
    return sprints


def check_sprint_calendar(sprints: list[Sprint], result: CheckResult) -> None:
    """Numbering runs 1..N and the dates do not overlap or run backwards."""
    numbers = [sprint.number for sprint in sprints]
    if numbers != list(range(1, len(numbers) + 1)):
        result.error(f"Sprint numbers must run 1..{len(numbers)} in order; the table has {numbers}")

    for sprint in sprints:
        if sprint.start and sprint.end and sprint.end < sprint.start:
            result.error(f"Sprint {sprint.number} ends ({sprint.end}) before it starts")

    for earlier, later in zip(sprints, sprints[1:]):
        if earlier.end and later.start and later.start <= earlier.end:
            result.error(
                f"Sprint {later.number} starts {later.start}, on or before Sprint "
                f"{earlier.number} ends {earlier.end}; a backlog cannot be frozen for "
                "two sprints at once"
            )


def check_sprint_deliverables(sprints: list[Sprint], result: CheckResult) -> None:
    """Each of D01–D05 is due in exactly one sprint."""
    if not sprints:
        return

    where: dict[str, list[int]] = {}
    for sprint in sprints:
        for deliverable in sprint.deliverables:
            where.setdefault(deliverable, []).append(sprint.number)

    for deliverable in DELIVERABLES:
        landed = where.get(deliverable, [])
        if not landed:
            result.error(
                f"No sprint is responsible for {deliverable}; every deliverable needs the "
                "sprint it is due in, or nobody can be marked late for it"
            )
        elif len(landed) > 1:
            joined = ", ".join(str(number) for number in landed)
            result.error(
                f"{deliverable} is due in sprints {joined}; each deliverable belongs to "
                "exactly one sprint"
            )

    for unknown in sorted(set(where) - set(DELIVERABLES)):
        result.error(f"Sprint table lists {unknown}, which is not one of {', '.join(DELIVERABLES)}")


def check_sprint_references(text: str, label: str, count: int, result: CheckResult) -> None:
    """Every "Sprint N" the learner reads has to exist in the spec's calendar."""
    if count <= 0:
        return
    out_of_range = sorted(
        {
            int(match.group(1))
            for match in _SPRINT_REFERENCE.finditer(text)
            if not 1 <= int(match.group(1)) <= count
        }
    )
    for number in out_of_range:
        result.error(
            f"{label} refers to Sprint {number} but the spec's calendar defines {count} sprint(s)"
        )


def check_checkpoint_gates(spec_text: str, result: CheckResult) -> None:
    """The spec names every standing gate, with its id, in one place."""
    body = section_body(spec_text, "## Sprint checkpoint")
    if not body:
        result.error(
            "Project spec has no '## Sprint checkpoint' section; without it a sprint "
            "boundary is a date, not a checkpoint"
        )
        return
    for gate, name in CHECKPOINT_GATES.items():
        if not re.search(rf"\b{gate}\b", body):
            result.error(f"Sprint checkpoint does not define gate {gate} ({name})")


def check_deliverable_coverage(
    rubric_text: str,
    sprint_count: int,
    result: CheckResult,
) -> None:
    tasks = parse_rubric_tasks(rubric_text)
    if not tasks:
        # long_form.verify already reports the missing task list.
        return

    joined = " ".join(task["name"] for task in tasks)
    for deliverable in DELIVERABLES:
        occurrences = len(re.findall(rf"\b{deliverable}\b", joined))
        if occurrences == 0:
            result.error(
                f"Rubric task list does not cover {deliverable}; each of "
                f"{', '.join(DELIVERABLES)} needs its own task"
            )
        elif occurrences > 1:
            result.error(f"Rubric task list covers {deliverable} {occurrences} times")

    sprint_tasks = [task for task in tasks if "sprint" in task["name"].lower()]
    contribution_tasks = [
        task
        for task in tasks
        if any(marker in task["name"].lower() for marker in CONTRIBUTION_MARKERS)
    ]

    if not contribution_tasks:
        result.error(
            "Rubric has no individual-contribution task; without one every member of a "
            "team receives the team's mark regardless of what they did"
        )

    if sprint_count >= 2 and not sprint_tasks:
        result.error(
            f"Spec runs {sprint_count} sprints but the rubric has no sprint-process task; "
            "the checkpoint scores have nowhere to land in the final grade"
        )
    if len(sprint_tasks) > 1:
        names = ", ".join(f"{task['id']} {task['name']!r}" for task in sprint_tasks)
        result.error(f"Rubric has more than one sprint-process task ({names})")

    overlap = [task for task in sprint_tasks if task in contribution_tasks]
    if overlap:
        task = overlap[0]
        result.error(
            f"{task['id']} {task['name']!r} scores both the team's sprint process and the "
            "individual; split them, or a strong member on a late team is punished twice"
        )


def check_gate_caps(rubric_text: str, result: CheckResult) -> None:
    """A gate is only a gate if missing it costs something in the final grade."""
    body = section_body(rubric_text, "## 4. Caps and Deductions")
    if not body:
        # long_form.verify already reports the missing section.
        return

    referenced = {gate for gate in CHECKPOINT_GATES if re.search(rf"\b{gate}\b", body)}
    if not referenced:
        result.error(
            "Rubric's Caps and Deductions section never names a sprint gate "
            f"({'–'.join((min(CHECKPOINT_GATES), max(CHECKPOINT_GATES)))}); a checkpoint "
            "nobody is capped for is a suggestion"
        )
        return

    missing = sorted(set(CHECKPOINT_GATES) - referenced)
    if missing:
        result.warn(
            f"Caps and Deductions names no consequence for {', '.join(missing)}; "
            "either give the gate a cap or drop it from the checkpoint"
        )


def verify(
    *,
    brief_path: str | None,
    spec_path: str | None,
    rubric_path: str | None,
    result: CheckResult,
) -> None:
    sprints: list[Sprint] = []

    if not spec_path:
        result.error("capstone_project verification requires --spec")
    else:
        spec = Path(spec_path)
        check_spec(spec, result)
        if spec.exists():
            spec_text = spec.read_text(encoding="utf-8")
            sprints = parse_sprints(spec_text, result)
            check_sprint_calendar(sprints, result)
            check_sprint_deliverables(sprints, result)
            check_checkpoint_gates(spec_text, result)

    # The brief and rubric are read again rather than passed in: long_form has
    # already reported them missing, and re-reporting it here is noise.
    if brief_path and Path(brief_path).exists():
        check_sprint_references(
            Path(brief_path).read_text(encoding="utf-8"), "Brief", len(sprints), result
        )

    if rubric_path:
        rubric_text = read_text(Path(rubric_path), result, label="rubric")
        if rubric_text:
            check_deliverable_coverage(rubric_text, len(sprints), result)
            check_gate_caps(rubric_text, result)
            check_sprint_references(rubric_text, "Rubric", len(sprints), result)
