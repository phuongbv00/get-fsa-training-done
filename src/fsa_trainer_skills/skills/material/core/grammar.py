"""What a teaching document is shaped like.

The corpus this generalises holds three generations of lecture note. The newest
— 24 of 46 files, across the three most recently authored modules — is the one
worth standardising on, and it is the `unit` template below. The `chapter`
template is the older form still used by two modules and is recognised so those
files can be checked rather than rewritten.

This table is the single source for `references/structure.md`. Prose describing
a required section the checker does not enforce would calibrate the model to a
constraint nothing holds it to, which is the same reason the programme skill
generates its rulebook.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Fence languages seen across the corpus. `text` is the workhorse for things
#: that are not code at all — ASCII diagrams, console output, directory trees.
FENCE_LANGUAGES = (
    "bash",
    "css",
    "dockerfile",
    "html",
    "http",
    "java",
    "javascript",
    "js",
    "json",
    "jsx",
    "properties",
    "python",
    "sh",
    "sql",
    "text",
    "ts",
    "tsx",
    "typescript",
    "xml",
    "yaml",
    "yml",
)

#: Reserved filename slots.
HANDBOOK_INDEX = "00"
APPENDIX_INDEX = "99"

#: `NN_Topic_Name.md`, with an optional letter for an out-of-syllabus aside.
NOTE_FILENAME = re.compile(r"^(\d{2})([a-z]?)_[A-Za-z0-9_&+-]+\.md$")
LAB_FILENAME = re.compile(r"^[a-z0-9]+_lab_(\d{2})\.md$")

#: A translation, not a rewrite: English is the default for everything.
TRANSLATION_SUFFIX = "_vn"


@dataclass(frozen=True)
class Slot:
    """One section a document must or may carry."""

    #: Any of these headings satisfies the slot.
    names: tuple[str, ...]
    required: bool = True
    #: First prose line under the heading must match, when given.
    opening: re.Pattern | None = None
    description: str = ""

    @property
    def label(self) -> str:
        return " / ".join(self.names)


@dataclass(frozen=True)
class Template:
    key: str
    title: str
    summary: str
    #: `# Chapter 3 · Effects` for a chapter, a bare title for a unit.
    heading: re.Pattern
    #: Sections between the objectives slot and the terminal ones are numbered
    #: contiguously and named by the author.
    numbered_sections: bool
    slots: tuple[Slot, ...] = field(default_factory=tuple)
    footer: re.Pattern | None = None
    footer_description: str = ""


AFTER_UNIT = re.compile(r"^After this unit, learners can:", re.IGNORECASE)
AFTER_CHAPTER = re.compile(r"^After this chapter, learners can:", re.IGNORECASE)

UNIT = Template(
    key="unit",
    title="Lecture note (unit)",
    summary=(
        "The current form, and what a new note should follow. A numbered "
        "objectives section, the concept sections, then a knowledge check and "
        "somewhere to go next."
    ),
    heading=re.compile(r"^# .+"),
    numbered_sections=True,
    slots=(
        Slot(
            names=("Objectives",),
            opening=AFTER_UNIT,
            description="What a learner can do afterwards; verb-initial bullets.",
        ),
        Slot(
            names=("Worked Example", "Classroom Demo Flow", "Complete Flow"),
            required=False,
            description="One runnable example composing the unit's concepts.",
        ),
        Slot(
            names=("Common Problems", "Common Mistakes", "Common Misconceptions"),
            required=False,
            description="Symptoms as sub-headings, so a learner can search for the error they hit.",
        ),
        Slot(
            names=("Practical Guidelines", "Design Checklist", "Review Checklist"),
            required=False,
            description="What to do in practice, as imperatives.",
        ),
        Slot(
            names=("Knowledge Check", "Quick Check"),
            description="A numbered question list, at least five, with no answers.",
        ),
        Slot(
            names=("Further Reading", "Hands-on Practice"),
            description="Where to go next: primary sources, or something to build.",
        ),
    ),
)

CHAPTER = Template(
    key="chapter",
    title="Lecture note (chapter)",
    summary=(
        "The older form, kept so existing modules can be checked. Prefer the "
        "unit template for anything new."
    ),
    heading=re.compile(r"^# Chapter \d+ · .+"),
    numbered_sections=True,
    slots=(
        Slot(names=("Objective",), opening=AFTER_CHAPTER, description="As above."),
        Slot(
            names=("Sub-topic Map",),
            required=False,
            description="A diagram of the chapter's shape.",
        ),
        Slot(names=("Real-world use",), description="Where this shows up in real work."),
        Slot(
            names=("Self-check checklist",),
            description="GitHub task-list items a learner ticks off.",
        ),
    ),
    footer=re.compile(r"^(Next|Review):\s*\[(?P<target>[^\]]+)\]\((?P<href>[^)]+)\)"),
    footer_description="A `Next:` or `Review:` line linking the sibling that follows.",
)

HANDBOOK = Template(
    key="handbook",
    title="Module handbook",
    summary="Slot `00`: how to study the module, what to install, what it assumes.",
    heading=re.compile(r"^# .+"),
    numbered_sections=True,
    slots=(),
)

APPENDIX = Template(
    key="appendix",
    title="Module appendix",
    summary=(
        "Slot `99`: the syllabus map with a link into the note that covers each "
        "outline item, plus the reference list. Largely derivable."
    ),
    heading=re.compile(r"^# .+"),
    numbered_sections=False,
    slots=(),
)

LAB = Template(
    key="lab",
    title="Lab guide",
    summary=(
        "The guided middle a session plan asks for and the corpus is missing: "
        "shorter than an assignment, step-numbered, with a checkable outcome."
    ),
    heading=re.compile(r"^# .+"),
    numbered_sections=False,
    slots=(
        Slot(
            names=("Objectives",),
            description="The objective codes this lab serves, from the session plan.",
        ),
        Slot(
            names=("Before you start", "Setup"),
            required=False,
            description="What must already work.",
        ),
        Slot(
            names=("Steps",), description="An ordered list; each step leaves something observable."
        ),
        Slot(
            names=("Acceptance", "Done when"),
            description="A task list a learner can check themselves against.",
        ),
    ),
)

TEMPLATES = (UNIT, CHAPTER, HANDBOOK, APPENDIX, LAB)
BY_KEY = {template.key: template for template in TEMPLATES}

#: The heading a lab must carry to declare which session it serves.
LAB_DURATION = re.compile(r"^\*\*Duration:\*\*\s*(\d+)\s*min", re.IGNORECASE | re.MULTILINE)
OBJECTIVE_CODE = re.compile(r"\b[A-Z][A-Z0-9]*-[A-Z]\d+\b")

#: Vietnamese-specific letters. Latin-1 accents alone are not evidence.
VIETNAMESE = re.compile("[ăâđêôơưĂÂĐÊÔƠƯ]|[Ạ-ỹ]|[̣̀́̃̉]")


def template_for(filename: str) -> Template | None:
    """Which template a filename claims, by its reserved slot or its shape."""
    if LAB_FILENAME.match(filename):
        return LAB
    match = NOTE_FILENAME.match(filename)
    if not match:
        return None
    index = match.group(1)
    if index == HANDBOOK_INDEX:
        return HANDBOOK
    if index == APPENDIX_INDEX:
        return APPENDIX
    return UNIT


__all__ = [
    "APPENDIX",
    "APPENDIX_INDEX",
    "BY_KEY",
    "CHAPTER",
    "FENCE_LANGUAGES",
    "HANDBOOK",
    "HANDBOOK_INDEX",
    "LAB",
    "LAB_DURATION",
    "LAB_FILENAME",
    "NOTE_FILENAME",
    "OBJECTIVE_CODE",
    "TEMPLATES",
    "TRANSLATION_SUFFIX",
    "UNIT",
    "VIETNAMESE",
    "Slot",
    "Template",
    "template_for",
]
