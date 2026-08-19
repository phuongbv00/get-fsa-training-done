"""Capstone-project verification, on top of the shared long-form checks.

A capstone differs from an assignment in three ways that need checking:

* Its tasks are the five programme deliverables D01–D05, so the rubric's task
  list must cover each of them exactly once and in order.
* It is team work, so the rubric needs a task that scores the individual, or
  every member of a team gets the team's mark regardless of contribution.
* It references sprints, a stack, and a demo — things the existing hand-written
  Mock Project material mentions but never defines. The spec document is where
  those get pinned down, so its fields are required rather than optional.
"""

from __future__ import annotations

import re
from pathlib import Path

from .common import CheckResult, read_text
from .long_form import parse_rubric_tasks

#: The programme's five deliverables. The rubric maps these onto T1..T5.
DELIVERABLES = ("D01", "D02", "D03", "D04", "D05")

#: Fields the spec must pin down. Each maps to something the current Mock
#: Project files refer to without ever defining.
REQUIRED_SPEC_FIELDS = {
    "Team size": ("team size", "quy mô nhóm", "số thành viên"),
    "Duration": ("duration", "thời lượng", "thời gian"),
    "Sprints": ("sprint",),
    "Stack": ("stack", "công nghệ", "technology"),
    "Demo": ("demo", "bảo vệ", "presentation", "trình bày"),
    "Contribution": ("contribution", "đóng góp", "individual"),
}

#: Words that mark a rubric task as scoring the individual rather than the team.
CONTRIBUTION_MARKERS = (
    "contribution",
    "individual",
    "per-member",
    "đóng góp",
    "cá nhân",
)


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


def check_deliverable_coverage(rubric_text: str, result: CheckResult) -> None:
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

    if not any(marker in task["name"].lower() for task in tasks for marker in CONTRIBUTION_MARKERS):
        result.error(
            "Rubric has no individual-contribution task; without one every member of a "
            "team receives the team's mark regardless of what they did"
        )


def verify(
    *,
    brief_path: str | None,
    spec_path: str | None,
    rubric_path: str | None,
    result: CheckResult,
) -> None:
    del brief_path  # already checked by the shared long-form pass

    if not spec_path:
        result.error("capstone_project verification requires --spec")
    else:
        check_spec(Path(spec_path), result)

    if rubric_path:
        rubric_text = read_text(Path(rubric_path), result, label="rubric")
        if rubric_text:
            check_deliverable_coverage(rubric_text, result)
