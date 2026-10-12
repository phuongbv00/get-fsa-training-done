"""The appendix's syllabus map, derived from the syllabus and the session plan.

The map is a mechanical transcription: each outline item, a tick box, and a link
into the note that covers it. Written by hand it rots the moment a heading is
renamed — and the anchors are the only deep links in the corpus, so nothing else
would notice.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from . import dom, i18n
from .grammar import APPENDIX_INDEX, HANDBOOK_INDEX, NOTE_FILENAME

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


MAP_SECTION = re.compile(
    r'(<section\b[^>]*data-part="syllabus-map"[^>]*>)(.*?)(</section>)', re.DOTALL
)


def teaching_notes(directory: Path) -> list[Path]:
    found = []
    for path in sorted(directory.glob("*.html")):
        match = NOTE_FILENAME.match(path.name)
        if match and match.group(1) not in (HANDBOOK_INDEX, APPENDIX_INDEX):
            found.append(path)
    return found


def _words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z]+", text.lower()) if len(word) > 3}


def _score(item: str, document: dom.Document) -> tuple[int, str]:
    """Like `_score`, against the note's title and its parts' headings and ids."""
    words = _words(item)
    if not words:
        return 0, ""
    best = (len(words & _words(document.title)), "")
    for section in document.body.find_all("section"):
        heading = section.find("h2")
        if heading is None or not section.get("id"):
            continue
        overlap = len(words & _words(heading.text()))
        if overlap > best[0]:
            best = (overlap, section.get("id"))
    return best


def render(syllabus_text: str, directory: Path, lang: str = "en") -> str:
    """The syllabus-map section's content: a heading and a checklist of links."""
    parsed = [(path, dom.parse(path)) for path in teaching_notes(directory)]
    heading = html.escape(i18n.t(lang, "Full Syllabus Map"))
    lines = ["", f"  <h2>{heading}</h2>", '  <ul class="checklist">']
    for item in outline_items(syllabus_text):
        best_path, best_id, best_score = None, "", 0
        for path, document in parsed:
            score, anchor = _score(item, document)
            if score > best_score:
                best_path, best_id, best_score = path, anchor, score
        label = html.escape(item)
        if best_path is None:
            lines.append(f"    <li>{label}</li>")
        else:
            index = NOTE_FILENAME.match(best_path.name).group(1)
            href = best_path.name + (f"#{best_id}" if best_id else "")
            lines.append(f'    <li>{label} → <a href="{href}">{index}</a></li>')
    lines.append("  </ul>")
    return "\n".join(lines) + "\n"


def patch(text: str, body: str) -> str:
    from get_fsa_training_done.errors import UsageError

    match = MAP_SECTION.search(text)
    if match is None:
        raise UsageError('the appendix has no <section data-part="syllabus-map">')
    return text[: match.start(2)] + body + text[match.end(2) :]


__all__ = ["outline_items", "patch", "render", "teaching_notes"]
