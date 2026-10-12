"""The lecture note's syllabus map, derived from the syllabus and the note's topics.

The map is a mechanical transcription: each outline item, a tick box, and a link
to the topic of the note that covers it. Written by hand it rots the moment a
heading is renamed, and nothing else would notice.
"""

from __future__ import annotations

import html
import re

from . import dom, i18n

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


#: Vietnamese words too common to say which topic an item belongs to.
STOP_WORDS = frozenset({"và", "của", "các", "với", "những", "một", "là", "để", "từ", "về"})


def _words(text: str) -> set[str]:
    """The words an outline item and a heading are matched on.

    English words of four letters or more. A Vietnamese syllable is short, and
    splitting at its diacritics would leave nothing, so any word carrying one
    counts whatever its length.
    """
    return {
        word
        for word in re.findall(r"\w+", text.lower())
        if word not in STOP_WORDS and (len(word) > 3 or not word.isascii())
    }


def topics(document: dom.Document) -> list[tuple[str, str]]:
    """Each topic part's id and heading, in order."""
    found = []
    for section in document.body.find_all("section"):
        heading = section.find("h2")
        if section.get("data-part") == "topic" and heading is not None and section.get("id"):
            found.append((section.get("id"), heading.text()))
    return found


def render(syllabus_text: str, document: dom.Document) -> str:
    """The syllabus-map part's content: a heading and a checklist of links.

    Each outline item links to the topic whose heading shares the most words
    with it, and is left unlinked when none does.
    """
    parts = topics(document)
    heading = html.escape(i18n.t(document.lang, "Full Syllabus Map"))
    lines = ["", f"  <h2>{heading}</h2>", '  <ul class="checklist">']
    for item in outline_items(syllabus_text):
        words = _words(item)
        best_id, best_label, best_score = "", "", 0
        for anchor, label in parts:
            score = len(words & _words(label))
            if score > best_score:
                best_id, best_label, best_score = anchor, label, score
        text = html.escape(item)
        if best_score:
            lines.append(
                f'    <li>{text} → <a href="#{best_id}">{html.escape(best_label)}</a></li>'
            )
        else:
            lines.append(f"    <li>{text}</li>")
    lines.append("  </ul>")
    return "\n".join(lines) + "\n"


#: Where a note without a map gets one: before Further Reading, or at the end.
MAP_PLACE = (
    re.compile(r'<section\b[^>]*data-part="further-reading"'),
    re.compile(r"</article>"),
)


def patch(text: str, body: str) -> str:
    """The note with its syllabus-map part's content replaced by `body`.

    The part is optional, so a note without one gets it in the grammar's place,
    before Further Reading.
    """
    from get_fsa_training_done.errors import UsageError

    match = MAP_SECTION.search(text)
    if match is not None:
        return text[: match.start(2)] + body + text[match.end(2) :]
    for place in MAP_PLACE:
        found = place.search(text)
        if found is not None:
            section = f'<section data-part="syllabus-map" id="syllabus-map">{body}</section>\n\n'
            return text[: found.start()] + section + text[found.start() :]
    raise UsageError(
        "the lecture note has no Further Reading part and no <article> to add the map to"
    )


__all__ = ["STOP_WORDS", "outline_items", "patch", "render", "topics"]
