"""Brief + rubric verification for the assignment, exam, and capstone types.

The load-bearing check is the cross-document one: task ids, names, and weights
have to agree between the brief the learner reads and the rubric the grader
scores from, because the rubric's fixed task list becomes the key structure of
every score sheet downstream. A rubric that has drifted from its brief produces
grades nobody can defend.
"""

from __future__ import annotations

import re
from pathlib import Path

from fsa_trainer_skills.levels import Level

from .. import budget as budget_mod
from ..pdf import count_pages
from . import calibration
from .common import CheckResult, normalize_name, read_text

REQUIRED_BRIEF_SECTIONS = [
    "## 1. Problem Statement",
    "## 2. Tasks",
    "## 3. Deliverables",
]

#: Retired in favour of per-task constraints and a leaner brief. Constraints now
#: live in the task they actually constrain, where the learner reads them at the
#: moment they matter.
RETIRED_BRIEF_SECTIONS = [
    "## 1. Context & Objective",
    "## 2. Prerequisites",
    "## 3. Constraints",
]

SCORING_GUIDE_SECTION = "## 3. Per-Task Scoring Guide"
CAPS_SECTION = "## 4. Caps and Deductions"
SCORE_SHEET_SECTION = "## 6. Score sheet"

REQUIRED_RUBRIC_SECTIONS = [
    "## 1. Grading Principle",
    "## 2. Fixed Task List",
    SCORING_GUIDE_SECTION,
    CAPS_SECTION,
    "## 5. Common point-loss reasons",
    SCORE_SHEET_SECTION,
]

#: The one subsection of section 4 that is not a task. It holds the failures
#: that sink the whole submission, and it costs nothing in reach: deducting `d`
#: from every task's raw score lowers `sum(score * weight) / 100` by exactly
#: `d`, and capping every task at `c` caps the total at `c`.
EVERY_TASK_HEADING = "### Every task"

#: Retired with the move to per-task caps. Both compute a final score by
#: adjusting the weighted total, and the score sheet has no field to record
#: that — it carries task scores and nothing else.
RETIRED_TOTAL_ADJUSTMENT = re.compile(r"^(Caps applied|Deductions)\s*:", re.IGNORECASE)

REQUIRED_BANNER_LINES = ["> **Code:**", "> **Duration:**", "> **Topics:**"]

#: Long unbroken paragraphs are the most common drafting defect: tasks should
#: lead with bullets stating outcomes, and prose past this length means the
#: learner has to extract requirements from a wall of text.
MAX_PARAGRAPH_WORDS = 70

#: Types whose task list is fixed by the programme rather than by the level.
#: A capstone always scores D01-D05, the sprint process, and the individual, so
#: comparing that count against the level's suggested range only ever produces a
#: warning nobody can act on.
FIXED_TASK_LIST_TYPES = ("capstone_project",)

_BRIEF_TASK = re.compile(
    r"^###\s+Task\s+(\d+)\s+[-–—]\s+(.+?)\s+\((\d+)%\)\s*$",
    re.MULTILINE,
)
_RUBRIC_TASK_ROW = re.compile(r"^\|\s*(T\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)%\s*\|", re.MULTILINE)
_RUBRIC_TASK_SECTION = re.compile(r"^###\s+(T\d+)\s+[-–—]")
#: Section 4 headings are matched loosely so a bare `### T3` is reported
#: rather than silently folded into the subsection above it.
_CAPS_TASK_HEADING = re.compile(r"^###\s+(T\d+)\b")


def section_body(text: str, heading: str) -> str:
    """The text under one `##` heading, up to the next one.

    Section-scoping matters more than it looks. The score sheet in section 6
    repeats every task id and weight, so parsing the fixed task list from the
    whole document double-counts them for any rubric that writes the id in its
    own cell (`| T1 | | 15% | |`) rather than inline with the name.
    """
    start = text.find(heading)
    if start == -1:
        return ""
    rest = text[start + len(heading) :]
    following = re.search(r"^##\s", rest, re.MULTILINE)
    return rest[: following.start()] if following else rest


def parse_brief_tasks(text: str) -> list[dict[str, str]]:
    return [
        {"id": f"T{number}", "name": name.strip(), "weight": weight}
        for number, name, weight in (m.groups() for m in _BRIEF_TASK.finditer(text))
    ]


def parse_rubric_tasks(text: str) -> list[dict[str, str]]:
    body = section_body(text, "## 2. Fixed Task List") or text
    return [
        {"id": m.group(1), "name": m.group(2).strip(), "weight": m.group(3)}
        for m in _RUBRIC_TASK_ROW.finditer(body)
        if m.group(2).strip()
    ]


def check_raw_point_sums(rubric_text: str, result: CheckResult) -> None:
    """Each per-task sub-criterion table must total exactly the declared 10.0.

    Scoped to section 3: section 4 now opens a `### Tn` subsection per task as
    well, and those tables carry caps, not sub-criterion points.
    """
    text = section_body(rubric_text, SCORING_GUIDE_SECTION)
    current_id: str | None = None
    running = 0.0
    saw_any = False

    for line in text.splitlines():
        section = _RUBRIC_TASK_SECTION.match(line)
        if section:
            current_id = section.group(1)
            running = 0.0
            continue
        if not current_id:
            continue

        declared = re.match(
            rf"^\|\s*\*\*{re.escape(current_id)} raw score\*\*\s*\|\s*"
            r"\*\*([0-9]+(?:\.[0-9]+)?)\*\*",
            line,
        )
        if declared:
            saw_any = True
            value = float(declared.group(1))
            if abs(running - value) > 0.001:
                result.error(
                    f"{current_id} sub-criteria sum to {running:g} but the row declares {value:g}"
                )
            if abs(value - 10.0) > 0.001:
                result.error(f"{current_id} declared raw score must be 10.0, not {value:g}")
            current_id = None
            running = 0.0
            continue

        points = re.match(r"^\|\s*(?!\*\*)[^|]+\|\s*([0-9]+(?:\.[0-9]+)?)\s*\|", line)
        if points:
            running += float(points.group(1))

    if not saw_any:
        result.error("Rubric has no per-task '**Tn raw score**' total rows")


def check_caps_are_per_task(
    rubric_text: str, rubric_tasks: list[dict[str, str]], result: CheckResult
) -> None:
    """Section 4 groups every cap and deduction under the task it bounds.

    A flat table cannot be graded twice the same way: `max 5.0` on its own says
    nothing about which score it bounds, and if the answer is the weighted
    total then the adjustment cannot be reproduced from the score sheet, which
    records task scores and nothing else.
    """
    body = section_body(rubric_text, CAPS_SECTION)
    if not body:
        # The missing section is already reported against REQUIRED_RUBRIC_SECTIONS.
        return

    known = {task["id"] for task in rubric_tasks}
    seen: list[str] = []
    scoped = False
    stray = 0

    for raw in body.splitlines():
        line = raw.strip()
        if line == EVERY_TASK_HEADING:
            if seen:
                result.error(
                    f"{CAPS_SECTION}: {EVERY_TASK_HEADING!r} must come before the task "
                    "subsections — it is what applies to all of them"
                )
            scoped = True
            continue
        heading = _CAPS_TASK_HEADING.match(line)
        if heading:
            task_id = heading.group(1)
            if not _RUBRIC_TASK_SECTION.match(line):
                result.error(
                    f"{CAPS_SECTION}: write the {task_id} subsection as "
                    f"'### {task_id} - <name>', so the grader reading a cap sees which "
                    "task it bounds"
                )
            if known and task_id not in known:
                result.error(
                    f"{CAPS_SECTION} has a {task_id} subsection but the fixed task "
                    f"list has no {task_id}"
                )
            elif task_id in seen:
                result.error(f"{CAPS_SECTION} lists {task_id} twice")
            seen.append(task_id)
            scoped = True
            continue
        if not scoped and line.startswith("|"):
            stray += 1

    if not seen:
        result.error(
            f"{CAPS_SECTION} has no '### Tn - <name>' subsections; every cap and "
            "deduction bounds one task's raw 0-10 score, so group them under the task "
            f"they belong to, with submission-wide failures under {EVERY_TASK_HEADING!r}"
        )
        return

    if stray:
        result.error(
            f"{CAPS_SECTION} has {stray} table line(s) before the first subsection; "
            "a cap or deduction that names no task is an adjustment to the weighted "
            "total, which the score sheet cannot record"
        )

    order = [int(task_id[1:]) for task_id in seen]
    if order != sorted(order):
        result.error(f"{CAPS_SECTION} subsections must run in task order, got {', '.join(seen)}")


def check_total_is_not_adjusted(rubric_text: str, result: CheckResult) -> None:
    """No step anywhere adjusts the weighted total after the tasks are scored."""
    if "final_before_deductions" in rubric_text:
        result.error(
            "Rubric computes a 'final_before_deductions'; caps and deductions are "
            "folded into the task score they bound, so the total is always "
            "`sum(task_score * weight) / 100`"
        )
    for raw in section_body(rubric_text, SCORE_SHEET_SECTION).splitlines():
        line = raw.strip()
        if RETIRED_TOTAL_ADJUSTMENT.match(line):
            result.error(
                f"{SCORE_SHEET_SECTION} carries a submission-level {line.split(':')[0]!r} "
                "line; the sheet records task scores only, with caps and deductions "
                "already folded into them"
            )


def check_page_budget(
    brief_text: str,
    pdf_path: str | None,
    max_pages: int | None,
    result: CheckResult,
) -> None:
    limit, source = budget_mod.page_budget_for(brief_text, override=max_pages)

    if limit is None:
        # Multi-day work is scoped by task count, not by how long the learner
        # sits with the brief, so there is nothing to enforce.
        return

    if pdf_path is None:
        result.warn(
            f"Page budget is {limit} A4 pages but no --pdf was given; "
            "render the brief with `fsa-trainer-skills assessment render` and re-check"
        )
        return

    pdf = Path(pdf_path)
    if not pdf.exists():
        result.error(f"Missing rendered brief PDF: {pdf}")
        return
    pages = count_pages(pdf)
    if pages is None:
        result.warn(f"Could not determine the page count of {pdf}")
        return
    if pages > limit:
        result.error(
            f"Brief renders to {pages} A4 pages but the budget is {limit} "
            f"(from {source}); cut content — re-rendering will not fix it"
        )


def check_prose_density(brief_text: str, result: CheckResult) -> None:
    """Warn on long unbroken paragraphs inside the Tasks section."""
    start = brief_text.find("## 2. Tasks")
    if start == -1:
        return
    end = brief_text.find("## 3. Deliverables", start)
    body = brief_text[start : end if end != -1 else len(brief_text)]

    in_fence = False
    paragraph: list[str] = []
    offenders: list[str] = []

    def flush() -> None:
        if not paragraph:
            return
        text = " ".join(paragraph)
        words = len(text.split())
        if words > MAX_PARAGRAPH_WORDS:
            offenders.append(f"{words} words: {text[:60]}...")
        paragraph.clear()

    for line in body.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            flush()
            continue
        if in_fence:
            continue
        stripped = line.strip()
        if (
            not stripped
            or stripped.startswith(("#", ">", "|", "-", "*", "$$"))
            or re.match(r"^\d+\.\s", stripped)
        ):
            flush()
            continue
        paragraph.append(stripped)
    flush()

    for offender in offenders:
        result.warn(
            f"Task paragraph exceeds {MAX_PARAGRAPH_WORDS} words ({offender}) — "
            "prefer bullets stating outcomes"
        )


def verify(
    *,
    assessment_type: str,
    brief_path: str | None,
    rubric_path: str | None,
    pdf_path: str | None,
    max_pages: int | None,
    result: CheckResult,
    level: Level | None = None,
) -> None:
    if not brief_path or not rubric_path:
        result.error(f"{assessment_type} verification requires --brief and --rubric")
        return

    brief = Path(brief_path)
    rubric = Path(rubric_path)
    brief_text = read_text(brief, result, label="brief")
    rubric_text = read_text(rubric, result, label="rubric")
    if not brief_text or not rubric_text:
        return

    if f"_{assessment_type}_" not in brief.name:
        result.warn(f"Brief filename does not contain '_{assessment_type}_': {brief.name}")
    if rubric.name != f"{brief.stem}_rubric.md":
        result.error(f"Rubric should be named {brief.stem}_rubric.md, not {rubric.name}")

    for needle in REQUIRED_BANNER_LINES:
        if needle not in brief_text:
            result.error(f"Brief is missing the header line {needle}")
    for section in REQUIRED_BRIEF_SECTIONS:
        if section not in brief_text:
            result.error(f"Brief is missing section: {section}")
    for section in RETIRED_BRIEF_SECTIONS:
        if section in brief_text:
            result.error(
                f"Brief uses the retired section {section!r}; state constraints inside "
                "the task they apply to and lead with '## 1. Problem Statement'"
            )

    check_page_budget(brief_text, pdf_path, max_pages, result)
    check_prose_density(brief_text, result)

    for needle in ["> **Code:**", "DO NOT distribute"]:
        if needle not in rubric_text:
            result.error(f"Rubric is missing the header or warning containing {needle}")
    for section in REQUIRED_RUBRIC_SECTIONS:
        if section not in rubric_text:
            result.error(f"Rubric is missing section: {section}")

    brief_tasks = parse_brief_tasks(brief_text)
    rubric_tasks = parse_rubric_tasks(rubric_text)
    if not brief_tasks:
        result.error("Brief has no '### Task N - Name (weight%)' headings")
    if not rubric_tasks:
        result.error("Rubric fixed task list has no Tn rows")

    brief_total = sum(int(task["weight"]) for task in brief_tasks)
    rubric_total = sum(int(task["weight"]) for task in rubric_tasks)
    if brief_tasks and brief_total != 100:
        result.error(f"Brief task weights sum to {brief_total}%, expected 100%")
    if rubric_tasks and rubric_total != 100:
        result.error(f"Rubric task weights sum to {rubric_total}%, expected 100%")

    if len(brief_tasks) != len(rubric_tasks):
        result.error(
            f"Task count mismatch: brief has {len(brief_tasks)}, rubric has {len(rubric_tasks)}"
        )

    if level is not None and brief_tasks and assessment_type not in FIXED_TASK_LIST_TYPES:
        calibration.check_task_count(len(brief_tasks), level, result)

    for index, (brief_task, rubric_task) in enumerate(zip(brief_tasks, rubric_tasks), start=1):
        expected = f"T{index}"
        if brief_task["id"] != expected or rubric_task["id"] != expected:
            result.error(f"Task ids must be sequential; expected {expected}")
        if brief_task["weight"] != rubric_task["weight"]:
            result.error(
                f"{expected} weight mismatch: brief {brief_task['weight']}%, "
                f"rubric {rubric_task['weight']}%"
            )
        if normalize_name(brief_task["name"]) != normalize_name(rubric_task["name"]):
            result.error(
                f"{expected} name mismatch: brief {brief_task['name']!r}, "
                f"rubric {rubric_task['name']!r}"
            )

    check_raw_point_sums(rubric_text, result)
    check_caps_are_per_task(rubric_text, rubric_tasks, result)
    check_total_is_not_adjusted(rubric_text, result)
