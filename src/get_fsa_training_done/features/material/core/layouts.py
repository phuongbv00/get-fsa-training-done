"""The slide layouts a deck may use, read from the FSA training-materials template.

This table is the single source for four things that must agree: the HTML a deck
is written in (`data-layout` and `data-slot`), the stylesheet that positions and
styles it (`theme/layouts.css`, generated), the rules `verify` applies, and the
placeholder each slot fills when `export pptx` writes into the real template.

Every value is the template's own — each slot's box as percentages of the slide,
and the size, weight, slant, face, colour, alignment and anchor PowerPoint
resolves for its placeholder. `tests/features/material/test_layouts.py` resolves
the same chain on the shipped `fsa_base.pptx` and fails on any difference that is
not listed in `DEVIATIONS` with its reason.

A title or a short text slot shrinks to fit, in steps (`FIT_SCALES`), by one
estimate (`fit_scale`) that the browser, PowerPoint and the PDF all apply, so the
three show the same size.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: 16:9, the template's slide size in points (9144000 x 5143500 EMU).
SLIDE_WIDTH_PT = 720
SLIDE_HEIGHT_PT = 405

#: What a slot may hold.
TITLE = "title"  # one line of inline text, shrunk to fit
TEXT = "text"  # a short run of inline text, shrunk to fit
BODY = "body"  # paragraphs, lists, code, an image, a table
PICTURE = "picture"  # an image only

#: The deck's skeleton, in order. `content` is any layout of that role.
COVER = "cover"
TOC = "toc"
OBJECTIVES = "objectives"
SECTION = "section"
CONTENT = "content"
SUMMARY = "summary"
CLOSING = "closing"

#: The faces the template names: the master's, the content layouts', and the
#: theme's minor font.
DISPLAY = "Segoe UI"
SANS = "Arial"
MINOR = "Calibri"

WHITE = "FFFFFF"
BLACK = "000000"
BRAND = "034EA1"
GREEN = "50B748"
GREY = "A6A6A6"
#: The 3 Columns and 3 Rows layouts' rules: tx1 at 50% luminance, 0.5pt.
RULE_COLOUR = "808080"
RULE_WIDTH_PT = 0.5

#: PowerPoint's default text insets, in points: 0.1in left and right, 0.05in
#: top and bottom. The stylesheet pads every slot by the same.
INSET_X = 7.2
INSET_Y = 3.6
#: The master sets 90% line spacing on titles and body text; at Arial's 1.15em
#: line that is about 1.05em.
LINE_HEIGHT = 1.05
#: How far a title or text slot may shrink, in order.
FIT_SCALES = (1.0, 0.9, 0.8, 0.7, 0.6)
#: Average advance of a character and of a space, in ems, for the fit estimate.
CHAR_EM = {False: 0.52, True: 0.57}
SPACE_EM = 0.28


@dataclass(frozen=True)
class Box:
    """A placeholder's position and size, as percentages of the slide."""

    left: float
    top: float
    width: float
    height: float

    @property
    def width_pt(self) -> float:
        return self.width / 100 * SLIDE_WIDTH_PT

    @property
    def height_pt(self) -> float:
        return self.height / 100 * SLIDE_HEIGHT_PT


@dataclass(frozen=True)
class Slot:
    name: str
    #: The placeholder's `idx` in the layout; None for a region the exporter
    #: fills with a shape of its own (the `Title only` layout's canvas).
    idx: int | None
    box: Box
    kind: str
    #: Points, as the template resolves them.
    size: int
    colour: str = BLACK
    bold: bool = False
    italic: bool = False
    font: str = SANS
    align: str = "left"  # left | center
    anchor: str = "top"  # top | middle | bottom
    required: bool = False
    #: Text the template shows as a prompt only; written out when the author
    #: leaves the slot out, so it appears in a slideshow.
    default: str = ""
    #: Most top-level list items a `body` slot should carry.
    max_items: int | None = None

    @property
    def fits(self) -> bool:
        """Does this slot shrink its text to fit?"""
        return self.kind in (TITLE, TEXT)


@dataclass(frozen=True)
class Layout:
    name: str
    pptx_name: str
    role: str
    #: The image under `theme/img/` the layout is drawn on.
    background: str
    summary: str
    slots: tuple[Slot, ...] = field(default_factory=tuple)
    #: Where the image sits when it does not fill the slide.
    background_box: Box | None = None
    #: Carries the template's copyright line and slide number.
    footer: bool = False
    #: The layout's ruled lines, drawn by the template rather than the
    #: background image: each a box with no width (vertical) or no height.
    rules: tuple[Box, ...] = ()

    def slot(self, name: str) -> Slot | None:
        for slot in self.slots:
            if slot.name == name:
                return slot
        return None

    @property
    def required(self) -> tuple[str, ...]:
        return tuple(slot.name for slot in self.slots if slot.required)


# --- Fitting text -------------------------------------------------------------


def lines_needed(text: str, width_pt: float, size: float, bold: bool) -> int:
    """How many lines `text` wraps to, word by word, at `size` in `width_pt`."""
    char = CHAR_EM[bold] * size
    space = SPACE_EM * size
    total = 0
    for paragraph in text.split("\n"):
        lines, used = 1, 0.0
        for word in paragraph.split():
            width = len(word) * char
            if used and used + space + width > width_pt:
                lines += 1
                used = 0.0
            else:
                used += space if used else 0
            # A word wider than the box breaks across lines (`overflow-wrap`).
            while used + width > width_pt and width > 0 and used == 0 and width > width_pt:
                lines += 1
                width -= width_pt
            used += width
        total += lines
    return max(total, 1)


def _fits_at(slot: Slot, text: str, scale: float) -> bool:
    """As many lines as the box holds — and always one, as the template's own
    single-line placeholders are sized for their text, not for its leading."""
    width = slot.box.width_pt - 2 * INSET_X
    height = slot.box.height_pt - 2 * INSET_Y
    size = slot.size * scale
    room = max(1, int((height + 0.5) // (size * LINE_HEIGHT)))
    return lines_needed(text, width, size, slot.bold) <= room


def fit_scale(slot: Slot, text: str) -> float:
    """The largest step of `FIT_SCALES` at which `text` fits `slot`'s box.

    The smallest step when nothing fits; `verify` reports that (`MAT-S08`).
    """
    if not slot.fits or not text.strip():
        return 1.0
    for scale in FIT_SCALES:
        if _fits_at(slot, text, scale):
            return scale
    return FIT_SCALES[-1]


def _sample(chars: int) -> str:
    """Prose-like text of `chars` characters: six-letter words and spaces."""
    return ("abcdef " * (chars // 7 + 1))[:chars].rstrip()


def title_budget(slot: Slot, scale: float = 1.0) -> int:
    """About how many characters a title or text slot holds before its type
    shrinks below `scale` of the template's size — the same estimate `verify`
    measures `MAT-S10` with, so a title written to it does not warn."""
    chars = 1
    while chars < 400 and fit_scale(slot, _sample(chars + 1)) >= scale:
        chars += 1
    return chars


def toc_budget() -> int:
    """About how many characters of a section title fit one table-of-contents
    row, which never shrinks its text: past that the .pptx wraps it."""
    _, (_, label) = TOC_ROWS[0]
    width = label.width_pt - 2 * INSET_X
    chars = 1
    while chars < 200 and lines_needed(_sample(chars + 1), width, TOC_SIZE, False) == 1:
        chars += 1
    return chars


def overflows(slot: Slot, text: str) -> bool:
    """Does `text` still not fit at the smallest step?"""
    return slot.fits and bool(text.strip()) and not _fits_at(slot, text, FIT_SCALES[-1])


# --- Shared geometry ------------------------------------------------------

#: The template's title placeholder spans the header band, but the logos sit in
#: its right third; a title is kept to the left two thirds (see DEVIATIONS).
BAND_TITLE = Box(4.4, 1.4, 62.0, 10.8)
#: The objectives layout's title sits a hair further right than the others'.
OBJECTIVES_TITLE = Box(4.58, 1.4, 62.0, 10.8)
BODY_FULL = Box(4.4, 18.3, 91.0, 73.8)


def _band_title(
    *, font: str = SANS, required: bool = True, default: str = "", box: Box = BAND_TITLE
) -> Slot:
    return Slot(
        "title",
        1,
        box,
        TITLE,
        size=36,
        colour=WHITE,
        bold=True,
        font=font,
        anchor="middle",
        required=required,
        default=default,
    )


def _top_title(top: float, height: float, *, font: str = SANS) -> Slot:
    """The title of the box, column and row layouts: a type-`title` placeholder."""
    return Slot(
        "title",
        0,
        Box(3.9, top, 62.0, height),
        TITLE,
        size=32,
        colour=WHITE,
        bold=True,
        font=font,
        anchor="middle",
        required=True,
    )


def _body(
    name: str,
    idx: int | None,
    box: Box,
    *,
    size: int = 24,
    items: int = 6,
    colour: str = BLACK,
    font: str = SANS,
) -> Slot:
    return Slot(name, idx, box, BODY, size=size, colour=colour, font=font, max_items=items)


def _closing(name: str, pptx_name: str, background: str, summary: str, colour: str, **extra):
    return Layout(
        name,
        pptx_name,
        CLOSING,
        background,
        summary,
        (
            Slot(
                "title",
                0,
                Box(4.9, 29.5, 40.1, 41.1),
                TITLE,
                size=48,
                colour=colour,
                bold=True,
                font=DISPLAY,
                anchor="middle",
                default="Thank you!",
            ),
        ),
        **extra,
    )


LAYOUTS: tuple[Layout, ...] = (
    Layout(
        "cover",
        "Cover Slide",
        COVER,
        "cover",
        "The first slide: the module, the lesson, where and when.",
        (
            Slot(
                "title",
                0,
                Box(4.9, 25.1, 54.9, 28.2),
                TITLE,
                size=48,
                colour=WHITE,
                bold=True,
                font=DISPLAY,
                anchor="middle",
                required=True,
            ),
            Slot(
                "lesson",
                11,
                Box(4.9, 57.0, 46.2, 7.3),
                TEXT,
                size=24,
                colour=WHITE,
                font=DISPLAY,
                required=True,
            ),
            Slot(
                "date",
                10,
                Box(4.9, 87.5, 14.5, 6.7),
                TEXT,
                size=9,
                colour=WHITE,
                font=DISPLAY,
                align="center",
                anchor="middle",
            ),
        ),
    ),
    Layout(
        "toc",
        "Table of Contents",
        TOC,
        "toc",
        "Derived from the section covers: write the slide empty, and the viewer and "
        "the exporter fill in up to five section titles.",
        (
            Slot(
                "title",
                0,
                Box(5.9, 27.6, 33.8, 34.8),
                TITLE,
                size=40,
                colour=BRAND,
                bold=True,
                anchor="middle",
                default="Table of Contents",
            ),
        ),
    ),
    Layout(
        "objectives",
        "1_Lesson Objectives",
        OBJECTIVES,
        "content",
        "Mandatory in the template. What a trainee can do after this lesson, each "
        "item citing the objective code it serves.",
        (
            _band_title(
                font=DISPLAY, required=False, default="Lesson Objectives", box=OBJECTIVES_TITLE
            ),
            _body("body", 10, Box(4.6, 17.0, 91.0, 74.7), items=5),
        ),
        footer=True,
    ),
    Layout(
        "section",
        "Section Cover #1",
        SECTION,
        "section",
        "Opens a section. The number is added from the section's position.",
        (
            Slot(
                "title",
                0,
                Box(4.9, 53.9, 74.3, 28.2),
                TITLE,
                size=48,
                colour=WHITE,
                bold=True,
                font=DISPLAY,
                anchor="middle",
                required=True,
            ),
            Slot(
                "subtitle",
                10,
                Box(4.9, 85.4, 34.2, 8.4),
                TEXT,
                size=21,
                colour=WHITE,
                italic=True,
                font=DISPLAY,
            ),
        ),
    ),
    Layout(
        "content",
        "Title and Content",
        CONTENT,
        "content",
        "The workhorse: a title and one body.",
        (_band_title(), _body("body", 10, BODY_FULL)),
        footer=True,
    ),
    Layout(
        "two-content",
        "Title and Two Content",
        CONTENT,
        "content",
        "Two bodies side by side: a comparison, a wrong/right pair, code beside its output.",
        (
            _band_title(),
            _body("left", 10, Box(4.6, 18.4, 42.0, 73.7), items=5),
            _body("right", 11, Box(53.4, 18.4, 42.0, 73.7), items=5),
        ),
        footer=True,
    ),
    Layout(
        "three-content",
        "Title and Three Content",
        CONTENT,
        "content",
        "Three bodies side by side.",
        (
            _band_title(),
            _body("left", 10, Box(4.4, 18.3, 30.1, 73.8), size=18, items=4),
            _body("middle", 11, Box(35.1, 18.3, 29.9, 73.8), size=18, items=4),
            _body("right", 12, Box(65.6, 18.3, 29.9, 73.8), size=18, items=4),
        ),
        footer=True,
    ),
    Layout(
        "subtitle-content",
        "Sub Title and Content",
        CONTENT,
        "content",
        "A title, a one-line framing under it, and a body.",
        (
            _band_title(),
            Slot("subtitle", 11, Box(4.4, 17.1, 91.2, 8.3), TEXT, size=28, required=True),
            _body("body", 10, Box(4.4, 28.1, 91.0, 64.0), items=5),
        ),
        footer=True,
    ),
    Layout(
        "title-only",
        "Title only",
        CONTENT,
        "content",
        "A title and a free canvas: a diagram, a screenshot, a table.",
        (_band_title(), _body("canvas", None, BODY_FULL, items=6)),
        footer=True,
    ),
    Layout(
        "content-picture",
        "Content and Picture",
        CONTENT,
        "content",
        "A body beside a picture.",
        (
            _band_title(),
            _body("body", 10, Box(4.6, 18.6, 48.6, 73.8), size=18, items=5),
            Slot("picture", 11, Box(56.0, 18.6, 39.6, 73.6), PICTURE, size=0, required=True),
        ),
        footer=True,
    ),
    Layout(
        "three-boxes",
        "3 Text Boxes",
        CONTENT,
        "boxes3",
        "Three labelled ideas on coloured cards, each explained under its card's label.",
        (
            _top_title(3.2, 7.8),
            Slot(
                "heading",
                10,
                Box(4.2, 18.1, 91.5, 7.8),
                TEXT,
                size=24,
                colour=BRAND,
                anchor="middle",
            ),
            *(
                Slot(
                    f"label-{n}",
                    idx,
                    Box(left, 33.2, 24.1, 15.7),
                    TEXT,
                    size=20,
                    colour=WHITE,
                    font=DISPLAY,
                    required=True,
                )
                for n, idx, left in ((1, 11, 7.2), (2, 13, 37.8), (3, 15, 68.4))
            ),
            *(
                _body(
                    f"body-{n}",
                    idx,
                    Box(left, 52.3, 24.1, 35.4),
                    size=12,
                    items=4,
                    colour=WHITE,
                    font=DISPLAY,
                )
                for n, idx, left in ((1, 17, 7.2), (2, 18, 37.8), (3, 19, 68.4))
            ),
        ),
        footer=True,
    ),
    Layout(
        "four-boxes",
        "4 Text Boxes",
        CONTENT,
        "boxes4",
        "Four labelled ideas on coloured cards.",
        (
            _top_title(3.5, 7.8),
            Slot(
                "heading",
                10,
                Box(4.2, 17.9, 91.2, 7.8),
                TEXT,
                size=24,
                colour=BRAND,
                anchor="middle",
            ),
            *(
                Slot(
                    f"label-{n}",
                    idx,
                    Box(left, 33.2, 18.5, 15.7),
                    TEXT,
                    size=20,
                    colour=WHITE,
                    font=DISPLAY,
                    required=True,
                )
                for n, idx, left in ((1, 11, 6.1), (2, 13, 29.1), (3, 15, 52.2), (4, 17, 75.5))
            ),
            *(
                _body(
                    f"body-{n}",
                    idx,
                    Box(left, 51.9, 18.5, 35.4),
                    size=12,
                    items=4,
                    colour=WHITE,
                    font=DISPLAY,
                )
                for n, idx, left in ((1, 18, 6.1), (2, 19, 29.1), (3, 20, 52.2), (4, 21, 75.5))
            ),
        ),
        footer=True,
    ),
    Layout(
        "three-columns",
        "3 Columns",
        CONTENT,
        "columns",
        "Three ruled columns, each with a heading, a body and an optional caption.",
        (
            _top_title(3.4, 7.7),
            *(
                Slot(
                    f"head-{n}",
                    idx,
                    Box(left, 19.1, 26.7, 6.5),
                    TEXT,
                    size=20,
                    colour=BRAND,
                    font=DISPLAY,
                    anchor="middle",
                    required=True,
                )
                for n, idx, left in ((1, 10, 3.9), (2, 21, 36.1), (3, 24, 68.7))
            ),
            *(
                _body(f"body-{n}", idx, Box(left, top, 26.7, 51.0), size=12, items=5, font=DISPLAY)
                for n, idx, left, top in (
                    (1, 27, 3.9, 28.8),
                    (2, 28, 36.2, 28.8),
                    (3, 29, 68.6, 28.5),
                )
            ),
            *(
                Slot(
                    f"caption-{n}",
                    idx,
                    Box(left, 83.2, 26.7, 5.7),
                    TEXT,
                    size=10,
                    colour=GREY,
                    font=DISPLAY,
                )
                for n, idx, left in ((1, 12, 3.9), (2, 23, 36.1), (3, 26, 68.7))
            ),
        ),
        footer=True,
        rules=(Box(33.52, 19.13, 0, 69.75), Box(65.74, 19.13, 0, 69.75)),
    ),
    Layout(
        "four-columns",
        "4 Columns Stacked",
        CONTENT,
        "columns",
        "A heading and an introduction across the top, four short bodies underneath.",
        (
            _top_title(2.6, 8.4, font=DISPLAY),
            Slot(
                "heading",
                10,
                Box(3.9, 19.1, 91.5, 6.5),
                TEXT,
                size=26,
                colour=BRAND,
                font=MINOR,
                anchor="middle",
            ),
            _body("intro", 11, Box(3.9, 29.4, 91.5, 21.8), size=12, items=3, font=DISPLAY),
            *(
                _body(f"body-{n}", idx, Box(left, top, 19.8, 35.2), size=14, items=4, font=DISPLAY)
                for n, idx, left, top in (
                    (1, 12, 3.9, 54.7),
                    (2, 13, 27.6, 54.53),
                    (3, 15, 51.6, 55.09),
                    (4, 14, 75.6, 55.09),
                )
            ),
        ),
        footer=True,
    ),
    Layout(
        "three-rows",
        "3 Rows",
        CONTENT,
        "columns",
        "Three ruled rows, a label on the left of each.",
        (
            _top_title(2.8, 9.1, font=DISPLAY),
            *(
                Slot(
                    f"label-{n}",
                    idx,
                    Box(3.9, top, 16.9, 18.2),
                    TEXT,
                    size=20,
                    colour=BRAND,
                    font=MINOR,
                    align="center",
                    anchor="middle",
                    required=True,
                )
                for n, idx, top in ((1, 10, 19.1), (2, 20, 45.8), (3, 18, 72.4))
            ),
            *(
                _body(f"body-{n}", idx, Box(22.7, top, 72.7, 18.2), size=14, items=3)
                for n, idx, top in ((1, 17, 19.1), (2, 21, 45.8), (3, 19, 72.4))
            ),
        ),
        footer=True,
        rules=(Box(3.89, 41.28, 91.53, 0), Box(3.89, 68.23, 91.53, 0)),
    ),
    Layout(
        "summary",
        "Lesson Summary",
        SUMMARY,
        "summary",
        "The template asks for the main points compared to the lesson objectives: "
        "one item per objective, each carrying `data-objective`.",
        (
            Slot(
                "title",
                1,
                Box(4.2, 3.3, 91.5, 10.8),
                TITLE,
                size=36,
                colour=BRAND,
                bold=True,
                font=DISPLAY,
                anchor="middle",
                default="Lesson Summary",
            ),
            _body("body", 10, Box(4.6, 17.0, 91.0, 74.7), items=6),
        ),
        footer=True,
    ),
    _closing(
        "closing",
        "Diversity",
        "thanks",
        "The last slide, on the template's photograph — the one its own sample uses.",
        WHITE,
    ),
    _closing(
        "closing-gradient",
        "1_Thank you",
        "thanks_gradient",
        "The last slide, on the gradient.",
        WHITE,
    ),
    _closing(
        "closing-illustration",
        "Thank you",
        "thanks_illustration",
        "The last slide, white, with the template's illustration on the right.",
        "B25E25",
        background_box=Box(52.3, 0.0, 47.7, 100.0),
    ),
)

BY_NAME = {layout.name: layout for layout in LAYOUTS}
BACKGROUNDS = tuple(dict.fromkeys(layout.background for layout in LAYOUTS))

#: Where this table departs from the template on purpose, and why. The fidelity
#: test allows exactly these and nothing else. `*` matches any layout or slot.
DEVIATIONS = {
    ("*", "title", "width"): "the header band's logos sit in its right third",
    ("three-rows", "body-*", "colour"): "the template's white text is invisible on white",
    ("three-rows", "body-*", "size"): "the template's 21pt does not fit a row",
    ("three-rows", "body-*", "font"): "set with the colour, to the content layouts' face",
}

#: The `Table of Contents` layout's five rows: a numbered circle and a section
#: title beside it, each a placeholder of its own, as (idx, box).
TOC_ROWS = (
    ((14, Box(42.9, 18.6, 5.2, 9.1)), (10, Box(50.0, 18.9, 44.1, 8.2))),
    ((15, Box(42.9, 32.7, 5.2, 9.1)), (11, Box(50.0, 33.3, 44.1, 8.2))),
    ((16, Box(42.9, 46.9, 5.2, 9.1)), (12, Box(50.0, 47.7, 44.1, 8.2))),
    ((17, Box(42.9, 60.3, 5.2, 9.1)), (13, Box(50.0, 61.0, 44.1, 8.2))),
    ((19, Box(42.9, 73.7, 5.2, 9.1)), (18, Box(50.1, 74.5, 44.1, 8.2))),
)
#: Both are white italic 20pt; the circle is filled green with a white ring.
TOC_SIZE = 20

#: Code on a slide is read from the back of a room.
MAX_CODE_LINES = 12
#: Code on a slide is set at this share of its slot's size, at most `CODE_MAX_PT`,
#: in a monospaced face whose characters are `CODE_CHAR_EM` wide.
CODE_SCALE = 0.62
CODE_MAX_PT = 14
CODE_CHAR_EM = 0.6


def code_size(slot: Slot) -> float:
    return min(round((slot.size or 18) * CODE_SCALE), CODE_MAX_PT)


def code_columns(slot: Slot) -> int:
    """How many characters of code fit across a slot, after the block's padding."""
    padding = 2 * INSET_X + 2 * 6 + 4  # the slot's insets, the block's, its rule
    return int((slot.box.width_pt - padding) // (code_size(slot) * CODE_CHAR_EM))


#: A slide's speaker notes are what the trainer says; a slide without them is a
#: slide only its author can present.
MIN_NOTE_WORDS = 15

__all__ = [
    "BACKGROUNDS",
    "BODY",
    "BY_NAME",
    "CLOSING",
    "CONTENT",
    "COVER",
    "DEVIATIONS",
    "FIT_SCALES",
    "LAYOUTS",
    "MAX_CODE_LINES",
    "MIN_NOTE_WORDS",
    "OBJECTIVES",
    "PICTURE",
    "SECTION",
    "SLIDE_HEIGHT_PT",
    "SLIDE_WIDTH_PT",
    "SUMMARY",
    "TEXT",
    "TITLE",
    "TOC",
    "TOC_ROWS",
    "title_budget",
    "toc_budget",
    "TOC_SIZE",
    "Box",
    "Layout",
    "Slot",
    "code_columns",
    "code_size",
    "fit_scale",
    "lines_needed",
    "overflows",
]
