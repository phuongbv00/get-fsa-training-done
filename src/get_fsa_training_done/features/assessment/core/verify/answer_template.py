"""Checks on the answer template a candidate fills in and submits.

A written exam is answered in a supplied Markdown file, so the file has to line
up with the brief: one heading per task, one slot per numbered question, and a
line for the candidate's account. It must not carry the questions themselves.
A template that quotes the brief is a second copy of the exam paper, and it
travels further than the brief does: it is opened, edited and handed back.
"""

from __future__ import annotations

import re
from pathlib import Path

from .common import CheckResult, normalize_name, read_text
from .long_form import section_body

CANDIDATE_LINE = "> **Candidate:**"

#: Shorter lines are instructions or labels ("Explain why."), which a template
#: may legitimately share with the brief. A question long enough to be worth
#: leaking is longer than this.
MIN_LEAK_WORDS = 8

_TEMPLATE_TASK = re.compile(r"^##\s+Task\s+(\d+)\s+[-–—]\s+(.+?)\s*$", re.MULTILINE)
_QUESTION_MARK = re.compile(r"\*\*Q(\d+)\.\*\*")
_MARKUP = re.compile(r"[*_`>#|]+")


def name_matches(brief: Path, template: Path, assessment_type: str) -> bool:
    """Whether the template's name follows its brief's.

    A theory exam's answer sheet is `<stem>_answer_template.md`; a practice
    exam's worksheet names what it holds, `<stem>[_<what>]_template.md`. A
    translation keeps `_vn` last in either.
    """
    stem = brief.stem.removesuffix("_vn")
    suffix = "_vn.md" if brief.stem.endswith("_vn") else ".md"
    name = template.name
    if not name.startswith(stem + "_") or not name.endswith("template" + suffix):
        return False
    if assessment_type == "practice_exam":
        return True
    return name == f"{stem}_answer_template{suffix}"


def _task_slots(text: str, heading: re.Pattern[str]) -> list[tuple[str, str, list[int]]]:
    """Each task heading in order, with the `**Qn.**` numbers under it in order."""
    tasks: list[tuple[str, str, list[int]]] = []
    for line in text.splitlines():
        found = heading.match(line)
        if found:
            tasks.append((f"T{found.group(1)}", found.group(2).strip(), []))
        elif tasks:
            tasks[-1][2].extend(int(n) for n in _QUESTION_MARK.findall(line))
    return tasks


_BRIEF_TASK_HEADING = re.compile(r"^###\s+Task\s+(\d+)\s+[-–—]\s+(.+?)\s+\(\d+%\)\s*$")
_TEMPLATE_TASK_HEADING = re.compile(r"^##\s+Task\s+(\d+)\s+[-–—]\s+(.+?)\s*$")


def _plain(text: str) -> str:
    return " ".join(_MARKUP.sub(" ", text).split()).lower()


def question_lines(brief_text: str) -> list[str]:
    """The lines of the Tasks section that carry question text."""
    lines: list[str] = []
    in_fence = False
    for raw in section_body(brief_text, "## 2. Tasks").splitlines():
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or raw.lstrip().startswith("#"):
            continue
        plain = _plain(_QUESTION_MARK.sub(" ", raw))
        plain = re.sub(r"^[-\d.)\s]+", "", plain)
        if len(plain.split()) >= MIN_LEAK_WORDS:
            lines.append(plain)
    return lines


def verify(
    *,
    assessment_type: str,
    brief_path: str,
    template_path: str,
    result: CheckResult,
) -> None:
    brief = Path(brief_path)
    template = Path(template_path)
    brief_text = read_text(brief, result, label="brief")
    template_text = read_text(template, result, label="answer template")
    if not brief_text or not template_text:
        return

    if not name_matches(brief, template, assessment_type):
        expected = (
            "<stem>[_<what>]_template.md"
            if assessment_type == "practice_exam"
            else "<stem>_answer_template.md"
        )
        result.warn(f"Answer template {template.name} should be named {expected}")

    if assessment_type == "theory_exam" and CANDIDATE_LINE not in template_text:
        result.error(f"Answer template is missing the {CANDIDATE_LINE} line")

    brief_tasks = _task_slots(section_body(brief_text, "## 2. Tasks"), _BRIEF_TASK_HEADING)
    template_tasks = _task_slots(template_text, _TEMPLATE_TASK_HEADING)
    by_id = {task_id: (name, slots) for task_id, name, slots in brief_tasks}

    if assessment_type == "practice_exam":
        # A worksheet serves the tasks whose output is writing: any of them,
        # in brief order, each under its exact brief name.
        ids = [task_id for task_id, _, _ in template_tasks]
        if ids != sorted(set(ids), key=lambda task_id: int(task_id[1:])):
            result.error("Worksheet task headings repeat or run out of order")
        for task_id, name, _ in template_tasks:
            if task_id not in by_id:
                result.error(f"Worksheet has {task_id} but the brief has no Task {task_id[1:]}")
            elif normalize_name(name) != normalize_name(by_id[task_id][0]):
                result.error(
                    f"Worksheet heading {task_id} {name!r} does not match brief "
                    f"{task_id} {by_id[task_id][0]!r}"
                )
    else:
        if len(template_tasks) != len(brief_tasks):
            result.error(
                f"Answer template has {len(template_tasks)} '## Task N - Name' headings, "
                f"the brief has {len(brief_tasks)} tasks"
            )
        for (b_id, b_name, b_slots), (t_id, t_name, t_slots) in zip(
            brief_tasks, template_tasks, strict=False
        ):
            if b_id != t_id or normalize_name(b_name) != normalize_name(t_name):
                result.error(
                    f"Answer template heading {t_id} {t_name!r} does not match brief "
                    f"{b_id} {b_name!r}"
                )
            elif t_slots != b_slots:
                result.error(
                    f"{t_id} has slots {_slot_list(t_slots)}; the brief asks "
                    f"{_slot_list(b_slots)}, once each and in that order"
                )

    plain_template = _plain(template_text)
    leaked = [line for line in question_lines(brief_text) if line in plain_template]
    for line in leaked:
        result.error(f"Answer template repeats the brief's question text: {line[:70]}...")


def _slot_list(slots: list[int]) -> str:
    return ", ".join(f"Q{n}" for n in slots) or "none"
