"""The rulebook for teaching material.

As in the programme skill: every finding names its rule, and
`references/structure.md` is generated from the same table the checker executes.

`MAT-D*` read one document, `MAT-S*` read one slide deck against the FSA
template, and `MAT-X*` are found while exporting. `MAT-C*` compare a module's
materials against the session plan that asks for them — the cross-feature half.
Ids are never reused: a gap in the numbering is a rule that was retired.
"""

from __future__ import annotations

from dataclasses import dataclass

from get_fsa_training_done.features.common.findings import ERROR, WARNING


@dataclass(frozen=True)
class Rule:
    id: str
    scope: str  # "document" | "deck" | "export" | "coverage"
    severity: str
    title: str
    rationale: str


RULES: tuple[Rule, ...] = (
    Rule(
        "MAT-D01",
        "document",
        ERROR,
        "The filename follows the module's naming convention",
        "The index orders the module and reserves 00 for the handbook and 99 "
        "for the appendix. A file outside the pattern sorts unpredictably, is "
        "never linked from either, and its kind cannot be told.",
    ),
    Rule(
        "MAT-D02",
        "document",
        ERROR,
        "Indexes are unique within a folder",
        "Two notes claiming the same position give the module two orders.",
    ),
    Rule(
        "MAT-D03",
        "document",
        WARNING,
        "Indexes run without a gap",
        "A gap usually means a note was deleted or never written; advisory "
        "because a module may deliberately leave room.",
    ),
    Rule(
        "MAT-D06",
        "document",
        ERROR,
        "The first section states what a learner will be able to do",
        "A note that opens with content has never said what it is for, and "
        "nothing downstream can map it to an objective.",
    ),
    Rule(
        "MAT-D08",
        "document",
        ERROR,
        "A note ends with a knowledge check and somewhere to go next",
        "Without them a note stops rather than closing, and a learner has no "
        "way to test what they just read.",
    ),
    Rule(
        "MAT-D09",
        "document",
        WARNING,
        "The knowledge check asks enough questions",
        "A check with one or two questions samples a fraction of the note.",
    ),
    Rule(
        "MAT-D10",
        "document",
        ERROR,
        "Every code block declares a language",
        "A block without `language-…` loses highlighting, and the convention is what "
        "lets `language-text` mark the blocks that are output rather than code.",
    ),
    Rule(
        "MAT-D11",
        "document",
        WARNING,
        "Code languages come from the known set",
        "An unrecognised tag is usually a typo; advisory because a module may "
        "legitimately introduce a new language.",
    ),
    Rule(
        "MAT-D12",
        "document",
        ERROR,
        "Relative links resolve to a file that exists",
        "A note pointing at a sibling that was renamed or never written sends "
        "the reader nowhere, and nothing reports it at render time.",
    ),
    Rule(
        "MAT-D13",
        "document",
        ERROR,
        "Link anchors resolve to an id in the target",
        "The appendix and the notes link into specific parts; renaming an id breaks them silently.",
    ),
    Rule(
        "MAT-D16",
        "document",
        WARNING,
        "The text is in the language the document declares",
        "`<html lang>` is what the theme, the exporters and the viewer follow for "
        'the words they write — a slide\'s default title, the "Try it" label, a '
        "PDF's session line. A module written in Vietnamese declares `vi`; a "
        "translation of an English original is a separate file ending `_vn`, "
        "so the original stays the thing every other document links to.",
    ),
    Rule(
        "MAT-D17",
        "document",
        ERROR,
        "A lab guide has ordered steps and a checklist of outcomes",
        "A lab without steps is an assignment brief, and one without an "
        "acceptance list leaves a learner unable to tell when they are done.",
    ),
    Rule(
        "MAT-D18",
        "document",
        WARNING,
        "A lab guide declares its duration",
        "The session plan allots it a number of minutes; a lab that never "
        "states one cannot be checked against that.",
    ),
    Rule(
        "MAT-D19",
        "document",
        WARNING,
        "An ER diagram states each relationship's cardinality in words",
        "Crow's-foot marks (`||--o{`) are read correctly only by someone who "
        "already knows the notation, which is what the diagram is teaching. "
        "A label beginning `1-1`, `1-n` or `n-n` says it plainly.",
    ),
    Rule(
        "MAT-D20",
        "document",
        WARNING,
        "A diagram takes its colours from the theme",
        "The material is read in light and dark mode. A colour fixed in the "
        "diagram is right in one and unreadable in the other, and it no longer "
        "matches the module's other diagrams.",
    ),
    Rule(
        "MAT-D21",
        "document",
        ERROR,
        "The document declares its kind, and the kind matches its filename",
        '`<meta name="fsa:kind">` is how the viewer, the exporter and `coverage` '
        "tell a deck from a note without guessing; a filename and a declaration "
        "that disagree mean one of them was copied from another file.",
    ),
    Rule(
        "MAT-D22",
        "document",
        ERROR,
        "The document uses the theme and no inline styling",
        "Every page links `_theme/fsa.css` and nothing else decides how it looks: "
        "no `style` attribute, no `<style>` element, no `<font>`. A one-off colour "
        "or size is how a module ends up with as many formats as authors, and it "
        "breaks dark mode and the exporters, which read the theme rather than the page.",
    ),
    Rule(
        "MAT-D23",
        "document",
        ERROR,
        "The HTML is well formed",
        "An unclosed element swallows whatever follows it — a slide into the next "
        "one, a section into the knowledge check — and a browser hides that by "
        "guessing, so the page looks right while the checker and exporter read "
        "something else.",
    ),
    Rule(
        "MAT-D24",
        "document",
        WARNING,
        "Every image says what it shows",
        "`alt` text is what a screen reader reads, what the exporter writes when "
        "an image cannot be placed, and what a trainee sees when it fails to load.",
    ),
    Rule(
        "MAT-D25",
        "document",
        ERROR,
        "Every knowledge-check question carries its answer",
        "A trainee working alone cannot tell a right answer from a wrong one "
        "without it. The answer sits in `<details>`, so it is there when wanted "
        "and hidden until then.",
    ),
    Rule(
        "MAT-D26",
        "document",
        WARNING,
        "Every objective is tested by a knowledge-check question",
        "An objective no question asks about is one a trainee can finish the "
        "lesson without ever checking; `data-objective` on each question makes "
        "the gap countable.",
    ),
    Rule(
        "MAT-D27",
        "document",
        WARNING,
        "A concept section explains before it shows",
        "Code with no sentence in front of it asks the trainee to reverse-engineer "
        "the point. The idea comes first, in prose; the example illustrates it.",
    ),
    Rule(
        "MAT-D28",
        "document",
        WARNING,
        "Every concept section gives the trainee something to try",
        "Reading is not practice. A short exercise straight after each idea, "
        "with its answer, is what turns a note into something a trainee learns "
        "from rather than skims.",
    ),
    Rule(
        "MAT-D29",
        "document",
        ERROR,
        "The parts a document must carry are present, in order",
        "Each kind has a fixed shape — the objectives first, the summary before "
        "the knowledge check — so a trainee finds the same thing in the same "
        "place in every lesson, and the checker can find it too.",
    ),
    Rule(
        "MAT-D30",
        "document",
        WARNING,
        "Every lab step says what the trainee should see",
        "A step without an expected result leaves the trainee unable to tell "
        "whether it worked until three steps later, when it is hard to say which "
        "one went wrong.",
    ),
    Rule(
        "MAT-D31",
        "document",
        ERROR,
        "Every objective item cites the objective code it serves",
        "`data-objective` on each objectives item is what `coverage`, the summary "
        "and the knowledge check are compared against; an item without one is an "
        "objective nothing can trace.",
    ),
    Rule(
        "MAT-S01",
        "deck",
        ERROR,
        "The deck follows the template's order",
        "Cover, an optional table of contents, Lesson Objectives — mandatory in "
        "the template — then each section opened by its section cover, then "
        "Lesson Summary and the closing slide. Trainees learn the rhythm once and "
        "every deck in the module then reads the same way.",
    ),
    Rule(
        "MAT-S02",
        "deck",
        ERROR,
        "Every slide uses a template layout, and only that layout's slots",
        "A slot is a placeholder in the real template; content outside one has "
        "nowhere to go when the deck is exported to PowerPoint, and an unknown "
        "layout has no background, no geometry and no placeholder at all.",
    ),
    Rule(
        "MAT-S03",
        "deck",
        ERROR,
        "A layout's required slots are filled",
        "A content slide with no title, or a cover with no lesson name, exports "
        "as the template's grey prompt text.",
    ),
    Rule(
        "MAT-S04",
        "deck",
        ERROR,
        "The objectives slide states the session's objectives",
        "Each item carries `data-objective`, and together they cover every code "
        "in `fsa:objectives` — the codes the session plan says this lesson serves.",
    ),
    Rule(
        "MAT-S05",
        "deck",
        ERROR,
        "The summary answers the objectives",
        "The template asks for the main points compared to the lesson objectives. "
        "Each summary item carries the `data-objective` it closes, and every "
        "objective is closed.",
    ),
    Rule(
        "MAT-S06",
        "deck",
        WARNING,
        "Every teaching slide has speaker notes",
        "Notes are what the trainer says over the slide — the explanation the "
        "slide compresses. Without them the deck can be presented only by its "
        "author, and it cannot later become a recorded lesson.",
    ),
    Rule(
        "MAT-S07",
        "deck",
        WARNING,
        "Every section has a check slide with its answer",
        'A question after each section — `data-role="check"`, the answer in '
        "`<details>` — makes trainees retrieve what they just saw, which is what "
        "fixes it; a deck that only presents is listened to and forgotten.",
    ),
    Rule(
        "MAT-S08",
        "deck",
        WARNING,
        "A slot stays within its layout's limits",
        "Each layout sets how many items, words or lines of code fit at the "
        "template's type size. Past that the text shrinks or spills, and a slide "
        "read from the back of a room stops being readable.",
    ),
    Rule(
        "MAT-S09",
        "deck",
        WARNING,
        "The number of slides fits the session's minutes",
        "Derived from `fsa:minutes` and `--minutes-per-slide`. Far too many slides "
        "for the time is a session that will be rushed or cut; far too few is one "
        "carried by the trainer's memory.",
    ),
    Rule(
        "MAT-S10",
        "deck",
        WARNING,
        "A title or short text keeps close to the template's size",
        "A slot's text shrinks to fit, but past a point (`--min-fit`, 70% by default) "
        "the deck's titles stop being one size: one slide's at 36pt, the next at 22pt. "
        "The fix is fewer words, not a smaller box.",
    ),
    Rule(
        "MAT-X01",
        "export",
        WARNING,
        "A diagram exported to a file has a rendered image",
        "Mermaid is drawn by the browser. PowerPoint and the PDF writer cannot "
        "run it, so a diagram needs an `<img>` of itself inside its `<figure>`, "
        "or it is exported as its source text.",
    ),
    Rule(
        "MAT-X02",
        "export",
        WARNING,
        "Every slot's content fits its placeholder",
        "Found while drawing the PDF: text that does not fit even after shrinking "
        "to the smallest readable size is cut, so the slide says less than its "
        "author wrote.",
    ),
    Rule(
        "MAT-X03",
        "export",
        WARNING,
        "Every image an export embeds is a PNG, JPEG or GIF inside the module",
        "PowerPoint and the PDF writer place raster images only, so an SVG has to be "
        "exported to PNG first. And an export embeds files from the module's own "
        "folder: a `src` reaching out with `../` would put an unrelated file into a "
        "deck handed to a class.",
    ),
    Rule(
        "MAT-C01",
        "coverage",
        ERROR,
        "Every material the session plan names exists",
        "The plan is a promise about what will be taught. A named file that "
        "does not exist is a session with nothing to deliver.",
    ),
    Rule(
        "MAT-C02",
        "coverage",
        WARNING,
        "Every material in the folder is used by a session",
        "A note nobody schedules is either unfinished or forgotten.",
    ),
    Rule(
        "MAT-C03",
        "coverage",
        WARNING,
        "A material's objective codes match the session that uses it",
        "The plan says which objectives a session serves; material claiming "
        "different ones is teaching to a different goal.",
    ),
    Rule(
        "MAT-C04",
        "coverage",
        WARNING,
        "Every objective code cited is defined in the syllabus",
        "A code the syllabus does not list is a typo or a missing objective.",
    ),
)

BY_ID = {rule.id: rule for rule in RULES}

__all__ = ["BY_ID", "RULES", "Rule"]
