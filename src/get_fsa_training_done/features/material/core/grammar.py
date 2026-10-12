"""What a teaching document is shaped like.

Material is written in HTML, one file per artifact, to the `KINDS` below: a
slide deck, a lecture note, a lab guide, the module handbook and appendix, and a
lab's worksheet. Each kind lists the `data-part` sections it carries, in order;
a deck's slides are described by `core/layouts.py` instead, because their shape
is the FSA template's.

This module and `layouts.py` are the single source for `references/material/
structure.md` and `layouts.md`. Prose describing a required section the checker
does not enforce would calibrate the model to a constraint nothing holds it to,
which is the same reason the programme skill generates its rulebook.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Code languages a block may declare as `language-…`. `text` is the workhorse
#: for things that are not code at all — console output, directory trees, error
#: text. Diagrams are `<pre class="mermaid">`, not a language.
CODE_LANGUAGES = (
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

#: A translation, not a rewrite: English is the default for everything.
TRANSLATION_SUFFIX = "_vn"

OBJECTIVE_CODE = re.compile(r"\b[A-Z][A-Z0-9]*-[A-Z]\d+\b")

#: Vietnamese-specific letters. Latin-1 accents alone are not evidence.
VIETNAMESE = re.compile("[ăâđêôơưĂÂĐÊÔƠƯ]|[Ạ-ỹ]|[̣̀́̃̉]")

#: `<meta name="fsa:...">` keys a document may carry.
META_KIND = "fsa:kind"
META_MODULE = "fsa:module"
META_SESSION = "fsa:session"
META_OBJECTIVES = "fsa:objectives"
META_MINUTES = "fsa:minutes"
META_STACK = "fsa:stack"

#: Where `material init` puts the theme, relative to the module folder.
THEME_DIR = "_theme"
THEME_CSS = f"{THEME_DIR}/fsa.css"
DECK_JS = f"{THEME_DIR}/deck.js"

#: `NN_Topic_Name.deck.html` per lesson, `<subject>_lecture_note.html` once per
#: module; `_vn` before the extension marks a translation.
DECK_FILENAME = re.compile(r"^(\d{2})([a-z]?)_[A-Za-z0-9_&+-]+?(?:_vn)?\.deck\.html$")
NOTE_FILENAME = re.compile(r"^([a-z0-9]+)_lecture_note(?:_vn)?\.html$")
#: `00_*` and `99_*`, and — before the note was one file per module — a
#: lesson's `NN_Topic_Name.html` beside its deck.
INDEXED_FILENAME = re.compile(r"^(\d{2})([a-z]?)_[A-Za-z0-9_&+-]+?(?:_vn)?(?<!\.deck)\.html$")
LAB_FILENAME = re.compile(r"^[a-z0-9]+_lab_(\d{2})(?:_vn)?\.html$")
WORKSHEET_FILENAME = re.compile(r"^[a-z0-9]+_lab_\d{2}_worksheet(?:_vn)?\.html$")


#: A code block's language, from `<code class="language-sql">`.
CODE_LANGUAGE = re.compile(r"\blanguage-([A-Za-z0-9+#-]+)\b")


@dataclass(frozen=True)
class Part:
    """One `<section data-part="...">` a document carries."""

    key: str
    heading: str
    required: bool = True
    #: A note has one `topic` part per lesson; every other part appears once.
    repeatable: bool = False
    description: str = ""


@dataclass(frozen=True)
class Kind:
    key: str
    title: str
    summary: str
    filename: re.Pattern
    #: The `<body>` class the theme styles it by.
    body_class: str
    parts: tuple[Part, ...] = ()
    required_meta: tuple[str, ...] = ()
    #: Most effective first: the order the module workflow writes them in.
    rank: int = 9

    def part(self, key: str) -> Part | None:
        for part in self.parts:
            if part.key == key:
                return part
        return None


DECK = Kind(
    key="deck",
    title="Slide deck",
    summary=(
        "What a session is taught from, on the FSA template. One `<section "
        'class="slide" data-layout="...">` per slide, slots marked `data-slot`, '
        'speaker notes in `<aside class="notes">`. The layouts and their slots '
        "are in `references/material/layouts.md`."
    ),
    filename=DECK_FILENAME,
    body_class="fsa-deck",
    required_meta=(META_KIND, META_MODULE, META_OBJECTIVES, META_MINUTES),
    rank=1,
)

HANDBOOK = Kind(
    key="handbook",
    title="Module handbook",
    summary=(
        "Slot `00`: the first page a trainee opens and the only one about the "
        "module as a whole — the lesson map, how to study, what to install."
    ),
    filename=re.compile(r"^00_[A-Za-z0-9_&+-]+?(?:_vn)?\.html$"),
    body_class="fsa-doc",
    required_meta=(META_KIND, META_MODULE),
    rank=2,
    parts=(
        Part(
            "module-map",
            "Module Map",
            description=(
                "A table, one row per lesson in order: its title, then a link to "
                "its deck, its topic in the lecture note and its lab where they exist."
            ),
        ),
        Part("how-to-study", "How to Study This Module", description="A routine per lesson."),
        Part(
            "environment",
            "Environment Setup",
            description="What to install, pinned to versions, and how to check it works.",
        ),
        Part(
            "running-domain",
            "The Running Example",
            required=False,
            description="The one domain every lesson's examples share.",
        ),
        Part("glossary", "Glossary", required=False, description="A `<dl>` of the module's terms."),
    ),
)

NOTE = Kind(
    key="note",
    title="Lecture note",
    summary=(
        "The module's theory, condensed into one file: what a trainee keeps as "
        "a reference and revises from before a theory exam or a job interview. "
        "One `topic` part per lesson, in the order of the decks — the decks "
        "teach, the note is what stays. Handed out as the HTML and its `.pdf`, "
        "never as a `.pptx`."
    ),
    filename=NOTE_FILENAME,
    body_class="fsa-doc",
    required_meta=(META_KIND, META_MODULE, META_OBJECTIVES),
    rank=3,
    parts=(
        Part(
            "objectives",
            "Objectives",
            description=(
                "Opens `After this module, learners can:`, then a list whose items "
                "each carry `data-objective` — every objective the module serves."
            ),
        ),
        Part(
            "topic",
            "<the lesson>",
            repeatable=True,
            description=(
                "One per lesson, in deck order: the theory condensed — definitions, "
                "the rules and why they hold, a minimal example, a comparison table "
                "where two things are easily confused. `<h3>` per point; prose "
                "before any example."
            ),
        ),
        Part(
            "misconceptions",
            "Common Misconceptions",
            required=False,
            description="One `<h3>` per wrong belief or easily confused pair, then what is true.",
        ),
        Part(
            "summary",
            "Summary",
            description=(
                "One item per objective, carrying `data-objective`: the page to reread "
                "the night before an exam."
            ),
        ),
        Part(
            "review-questions",
            "Review Questions",
            description=(
                "An `<ol>` of the questions a theory exam or an interviewer asks; each "
                "carries `data-objective` and a model answer in `<details>`."
            ),
        ),
        Part("further-reading", "Further Reading", description="Primary sources, linked."),
    ),
)

LAB = Kind(
    key="lab",
    title="Lab guide",
    summary=(
        "Guided practice: shorter than an assignment, step-numbered, and "
        "checkable by the trainee without a marker."
    ),
    filename=LAB_FILENAME,
    body_class="fsa-doc",
    required_meta=(META_KIND, META_MODULE, META_OBJECTIVES, META_MINUTES),
    rank=4,
    parts=(
        Part(
            "objectives",
            "Objectives",
            description="Opens `After this lab, learners can:`; items carry `data-objective`.",
        ),
        Part(
            "before-you-start",
            "Before You Start",
            required=False,
            description="What must already work; any starter project or worksheet.",
        ),
        Part(
            "steps",
            "Steps",
            description=(
                'An `<ol>`; each step ends in a `class="expected"` element saying '
                'what the trainee should see, with an optional `<details class="hint">`.'
            ),
        ),
        Part(
            "acceptance",
            "Acceptance",
            description='A `<ul class="checklist">` of outcomes the trainee can observe.',
        ),
        Part(
            "stretch",
            "Stretch",
            required=False,
            description="An extension for whoever finishes early.",
        ),
    ),
)

APPENDIX = Kind(
    key="appendix",
    title="Module appendix",
    summary="Slot `99`: the syllabus map, derived by `derive appendix`, and the references.",
    filename=re.compile(r"^99_[A-Za-z0-9_&+-]+?(?:_vn)?\.html$"),
    body_class="fsa-doc",
    required_meta=(META_KIND, META_MODULE),
    rank=6,
    parts=(
        Part(
            "syllabus-map",
            "Full Syllabus Map",
            description="Derived: each outline item and a link into the lecture note's topic.",
        ),
        Part("references", "References", required=False, description="The module's sources."),
    ),
)

WORKSHEET = Kind(
    key="worksheet",
    title="Lab worksheet",
    summary=(
        "The blank form each group fills in during a group lab: a heading and a "
        "drawn table per output. No parts are prescribed."
    ),
    filename=WORKSHEET_FILENAME,
    body_class="fsa-doc",
    required_meta=(META_KIND, META_MODULE),
    rank=5,
)

KINDS = (DECK, HANDBOOK, NOTE, LAB, WORKSHEET, APPENDIX)
KIND_BY_KEY = {kind.key: kind for kind in KINDS}


def kind_for(filename: str) -> Kind | None:
    """Which HTML kind a filename claims. Order matters: a deck is also `NN_*.html`."""
    if WORKSHEET_FILENAME.match(filename):
        return WORKSHEET
    if LAB_FILENAME.match(filename):
        return LAB
    if DECK_FILENAME.match(filename):
        return DECK
    if NOTE_FILENAME.match(filename):
        return NOTE
    if INDEXED_FILENAME.match(filename):
        index = filename[:2]
        if index == HANDBOOK_INDEX:
            return HANDBOOK
        if index == APPENDIX_INDEX:
            return APPENDIX
    return None


def is_session_note(filename: str) -> bool:
    """`01_Topic.html` or `dbf_lecture_01.html`: a lecture note per session.

    The note is one file per module now; a name in the old shape is a note to
    fold into it, and saying so beats calling it an unknown name.
    """
    match = INDEXED_FILENAME.match(filename)
    if match and match.group(1) not in (HANDBOOK_INDEX, APPENDIX_INDEX):
        return True
    return bool(re.search(r"_lecture_\d+(?:_vn)?\.(?:html|md)$", filename))


def is_translation(filename: str) -> bool:
    stem = filename.split(".", 1)[0]
    return stem.endswith(TRANSLATION_SUFFIX)


__all__ = [
    "APPENDIX",
    "APPENDIX_INDEX",
    "CODE_LANGUAGE",
    "CODE_LANGUAGES",
    "DECK",
    "DECK_FILENAME",
    "DECK_JS",
    "HANDBOOK",
    "HANDBOOK_INDEX",
    "INDEXED_FILENAME",
    "KINDS",
    "KIND_BY_KEY",
    "Kind",
    "LAB_FILENAME",
    "LAB",
    "META_KIND",
    "META_MINUTES",
    "META_MODULE",
    "META_OBJECTIVES",
    "META_SESSION",
    "META_STACK",
    "NOTE",
    "NOTE_FILENAME",
    "OBJECTIVE_CODE",
    "Part",
    "THEME_CSS",
    "THEME_DIR",
    "TRANSLATION_SUFFIX",
    "VIETNAMESE",
    "WORKSHEET_FILENAME",
    "WORKSHEET",
    "is_session_note",
    "is_translation",
    "kind_for",
]
