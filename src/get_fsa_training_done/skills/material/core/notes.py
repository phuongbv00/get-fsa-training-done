"""Reading a teaching document into the parts the checks care about.

Headings, fenced blocks, links and list items — nothing else. This is not a
Markdown renderer: the questions asked of a note are structural (is the first
section the objectives, are the numbers contiguous, does that link resolve), and
answering them from a token stream would be more machinery for less clarity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .grammar import FENCE_LANGUAGES

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
NUMBERED = re.compile(r"^(\d+)\.\s+(.*)$")
FENCE = re.compile(r"^\s*```\s*([A-Za-z0-9+#-]*)\s*$")
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
TASK_ITEM = re.compile(r"^\s*-\s+\[[ xX]\]\s+")
LIST_ITEM = re.compile(r"^\s*-\s+")


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    line: int
    #: The leading `N.` of `## 3. Effects`, when there is one.
    number: int | None = None
    #: The heading with its number stripped: `Effects`.
    title: str = ""

    def slug(self) -> str:
        """GitHub's anchor for this heading."""
        text = self.text.lower()
        text = re.sub(r"[^\w\s-]", "", text.replace("·", " "))
        return re.sub(r"[\s_]+", "-", text.strip()).strip("-")


@dataclass(frozen=True)
class Fence:
    language: str
    line: int


@dataclass
class Note:
    path: Path
    text: str
    lines: list[str]
    headings: list[Heading] = field(default_factory=list)
    fences: list[Fence] = field(default_factory=list)
    links: list[tuple[str, int]] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.headings[0].text if self.headings and self.headings[0].level == 1 else ""

    @property
    def sections(self) -> list[Heading]:
        return [heading for heading in self.headings if heading.level == 2]

    def body_of(self, heading: Heading) -> list[str]:
        """The lines under a heading, up to the next one at the same level."""
        start = heading.line
        for other in self.headings:
            if other.line > heading.line and other.level <= heading.level:
                return self.lines[start : other.line - 1]
        return self.lines[start:]

    def section_named(self, names: tuple[str, ...]) -> Heading | None:
        wanted = {name.lower() for name in names}
        for heading in self.sections:
            if heading.title.lower() in wanted:
                return heading
        return None

    def slugs(self) -> set[str]:
        return {heading.slug() for heading in self.headings}


def parse(path: Path) -> Note:
    from get_fsa_training_done.errors import UsageError

    if not path.is_file():
        raise UsageError(f"document not found: {path}")
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    note = Note(path=path, text=text, lines=lines)
    in_fence = False
    for number, line in enumerate(lines, start=1):
        fence = FENCE.match(line)
        if fence:
            if not in_fence:
                note.fences.append(Fence(language=fence.group(1), line=number))
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        heading = HEADING.match(line)
        if heading:
            raw = heading.group(2).strip()
            numbered = NUMBERED.match(raw)
            note.headings.append(
                Heading(
                    level=len(heading.group(1)),
                    text=raw,
                    line=number,
                    number=int(numbered.group(1)) if numbered else None,
                    title=numbered.group(2).strip() if numbered else raw,
                )
            )
        for match in LINK.finditer(line):
            note.links.append((match.group(1), number))
    return note


def first_prose(body: list[str]) -> str:
    for line in body:
        if line.strip():
            return line.strip()
    return ""


def numbered_items(body: list[str]) -> list[str]:
    return [match.group(2) for match in (NUMBERED.match(line) for line in body) if match]


def task_items(body: list[str]) -> list[str]:
    return [line.strip() for line in body if TASK_ITEM.match(line)]


def bullet_items(body: list[str]) -> list[str]:
    return [line.strip()[2:] for line in body if LIST_ITEM.match(line)]


def known_language(language: str) -> bool:
    return language.lower() in FENCE_LANGUAGES


__all__ = [
    "Fence",
    "Heading",
    "Note",
    "bullet_items",
    "first_prose",
    "known_language",
    "numbered_items",
    "parse",
    "task_items",
]
