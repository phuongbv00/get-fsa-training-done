"""The words the theme and the tools write into a document, in its language.

A document declares its language with `<html lang="…">`. Everything the skill
writes on the author's behalf — a slide's default title, the theme's "Try it"
label, a PDF's "Session 3 · 90 min" line, the appendix's map heading — follows
that declaration, so a module written in Vietnamese does not come out with
English chrome around it.

This table is the single source: `scripts/material/gen_layouts.py` generates
the stylesheet's labels from it, and the exporters and `derive` read it.
English is the fallback for a language with no entry.
"""

from __future__ import annotations

import re

DEFAULT = "en"

#: Each English string, and what it is in every other language the skill knows.
STRINGS: dict[str, dict[str, str]] = {
    # The template's slide defaults.
    "Lesson Objectives": {"vi": "Mục tiêu bài học"},
    "Table of Contents": {"vi": "Nội dung"},
    "Lesson Summary": {"vi": "Tóm tắt bài học"},
    "Thank you!": {"vi": "Cảm ơn!"},
    # The theme's labels.
    "Try it": {"vi": "Thử ngay"},
    "You should see:": {"vi": "Kết quả mong đợi:"},
    "Wrong": {"vi": "Sai"},
    "Right": {"vi": "Đúng"},
    "Answer": {"vi": "Đáp án"},
    # A document's line of facts.
    "Session": {"vi": "Buổi"},
    "min": {"vi": "phút"},
    # Derived content.
    "Full Syllabus Map": {"vi": "Bản đồ syllabus"},
    # The deck viewer's hint line.
    "N notes · O overview": {"vi": "N ghi chú · O tổng quan"},
    "No speaker notes for this slide.": {"vi": "Slide này không có ghi chú."},
}

#: The opening line of an objectives part, per language. `verify` accepts any
#: of them, and the templates write the one for the document's language.
AFTER = {
    "en": re.compile(r"^After this (unit|lesson|lab), (learners|you) can:", re.IGNORECASE),
    "vi": re.compile(
        r"^Sau (bài|buổi) (học|lab|thực hành)( này)?, (học viên|bạn) (có thể|sẽ):",
        re.IGNORECASE,
    ),
}


def language(code: str) -> str:
    """`vi-VN` → `vi`; an empty or unknown declaration is English."""
    base = (code or "").strip().lower().split("-", 1)[0]
    known = {lang for strings in STRINGS.values() for lang in strings} | {DEFAULT}
    return base if base in known else DEFAULT


def t(lang: str, text: str) -> str:
    """`text` in `lang`, or as it is when there is no translation."""
    return STRINGS.get(text, {}).get(language(lang), text)


def languages() -> tuple[str, ...]:
    """Every language with at least one translation, English first."""
    found = sorted({lang for strings in STRINGS.values() for lang in strings})
    return (DEFAULT, *found)


def opens_objectives(line: str) -> bool:
    return any(pattern.match(line) for pattern in AFTER.values())


__all__ = ["AFTER", "DEFAULT", "STRINGS", "language", "languages", "opens_objectives", "t"]
