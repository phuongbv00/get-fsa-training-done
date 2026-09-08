"""The appendix's syllabus map, derived from the syllabus and the session plan.

The map is a mechanical transcription: each outline item, a tick box, and a link
into the note that covers it. Written by hand it rots the moment a heading is
renamed — and the anchors are the only deep links in the corpus, so nothing else
would notice.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import notes
from .grammar import APPENDIX_INDEX, HANDBOOK_INDEX, NOTE_FILENAME

MAP_HEADING = "## A. Full Syllabus Map"
NEXT_HEADING = re.compile(r"^## [B-Z]\. ", re.MULTILINE)
OUTLINE_HEADING = "### 7. Topic Outline"
TIME_HEADING = "### 8. Time Allocation"


def outline_items(syllabus_text: str) -> list[str]:
    start = syllabus_text.find(OUTLINE_HEADING)
    if start < 0:
        return []
    end = syllabus_text.find(TIME_HEADING, start)
    body = syllabus_text[start : end if end > 0 else None]
    return [
        match.group(1).strip()
        for match in (re.match(r"^\d+\.\s+(.+)$", line) for line in body.splitlines())
        if match
    ]


def teaching_notes(directory: Path) -> list[Path]:
    found = []
    for path in sorted(directory.glob("*.md")):
        match = NOTE_FILENAME.match(path.name)
        if match and match.group(1) not in (HANDBOOK_INDEX, APPENDIX_INDEX):
            found.append(path)
    return found


def _score(item: str, note: notes.Note) -> tuple[int, str]:
    """How well a note covers an outline item, and which heading covers it best.

    Word overlap rather than anything cleverer: the outline and the headings are
    written by the same person about the same thing, and a wrong guess costs a
    link the author will correct, not a silent error.
    """
    words = {word for word in re.findall(r"[a-z]+", item.lower()) if len(word) > 3}
    if not words:
        return 0, ""
    best = (0, "")
    for heading in note.headings:
        if heading.level not in (1, 2):
            continue
        target = {word for word in re.findall(r"[a-z]+", heading.text.lower()) if len(word) > 3}
        overlap = len(words & target)
        if overlap > best[0]:
            best = (overlap, heading.slug())
    return best


def render(syllabus_text: str, directory: Path) -> str:
    """The `## A. Full Syllabus Map` section body."""
    parsed = [(path, notes.parse(path)) for path in teaching_notes(directory)]
    lines = []
    for item in outline_items(syllabus_text):
        best_path, best_slug, best_score = None, "", 0
        for path, note in parsed:
            score, slug = _score(item, note)
            if score > best_score:
                best_path, best_slug, best_score = path, slug, score
        if best_path is None:
            lines.append(f"- [ ] {item}")
        else:
            index = NOTE_FILENAME.match(best_path.name).group(1)
            anchor = f"#{best_slug}" if best_slug else ""
            lines.append(f"- [ ] {item} → [{index}]({best_path.name}{anchor})")
    return "\n".join(lines)


def patch(text: str, body: str) -> str:
    """Replace the map section, leaving the rest of the appendix alone."""
    from fsa_trainer_skills.errors import UsageError

    start = text.find(MAP_HEADING)
    if start < 0:
        raise UsageError(f"the appendix has no {MAP_HEADING!r} section")
    after = start + len(MAP_HEADING)
    match = NEXT_HEADING.search(text, after)
    end = match.start() if match else len(text)
    return f"{text[:after]}\n\n{body}\n\n{text[end:]}" if match else f"{text[:after]}\n\n{body}\n"


__all__ = ["MAP_HEADING", "outline_items", "patch", "render", "teaching_notes"]
