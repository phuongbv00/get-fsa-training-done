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
from .long_form import parse_brief_tasks, section_body

CANDIDATE_LINE = "> **Candidate:**"

#: Shorter lines are instructions or labels ("Explain why."), which a template
#: may legitimately share with the brief. A question long enough to be worth
#: leaking is longer than this.
MIN_LEAK_WORDS = 8

_TEMPLATE_TASK = re.compile(r"^##\s+Task\s+(\d+)\s+[-–—]\s+(.+?)\s*$", re.MULTILINE)
_QUESTION_MARK = re.compile(r"\*\*Q(\d+)\.\*\*")
_MARKUP = re.compile(r"[*_`>#|]+")


def expected_name(brief: Path) -> set[str]:
    """`<stem>_answer_template.md`, with a translation's `_vn` kept last."""
    stem = brief.stem
    names = {f"{stem}_answer_template.md"}
    if stem.endswith("_vn"):
        names.add(f"{stem[:-3]}_answer_template_vn.md")
    return names


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

    names = expected_name(brief)
    if template.name not in names:
        result.warn(f"Answer template should be named {' or '.join(sorted(names))}")

    if assessment_type == "theory_exam" and CANDIDATE_LINE not in template_text:
        result.error(f"Answer template is missing the {CANDIDATE_LINE} line")

    brief_tasks = parse_brief_tasks(brief_text)
    template_tasks = [
        {"id": f"T{number}", "name": name} for number, name in _TEMPLATE_TASK.findall(template_text)
    ]
    if template_tasks or assessment_type == "theory_exam":
        if len(template_tasks) != len(brief_tasks):
            result.error(
                f"Answer template has {len(template_tasks)} '## Task N - Name' headings, "
                f"the brief has {len(brief_tasks)} tasks"
            )
        for brief_task, template_task in zip(brief_tasks, template_tasks):
            if brief_task["id"] != template_task["id"] or normalize_name(
                brief_task["name"]
            ) != normalize_name(template_task["name"]):
                result.error(
                    f"Answer template heading {template_task['id']} "
                    f"{template_task['name']!r} does not match brief "
                    f"{brief_task['id']} {brief_task['name']!r}"
                )

    asked = sorted(
        {int(n) for n in _QUESTION_MARK.findall(section_body(brief_text, "## 2. Tasks"))}
    )
    if asked:
        slots = sorted({int(n) for n in _QUESTION_MARK.findall(template_text)})
        if slots != asked:
            result.error(
                f"Answer template has slots for Q{', Q'.join(map(str, slots)) or ' none'}; "
                f"the brief asks Q{asked[0]}-Q{asked[-1]}"
            )

    plain_template = _plain(template_text)
    leaked = [line for line in question_lines(brief_text) if line in plain_template]
    for line in leaked:
        result.error(f"Answer template repeats the brief's question text: {line[:70]}...")
