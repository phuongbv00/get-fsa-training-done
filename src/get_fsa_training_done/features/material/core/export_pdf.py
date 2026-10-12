"""Write material to PDF: a deck slide by slide, a document page by page.

A deck is drawn with reportlab, which `xhtml2pdf` already brings into the
managed venv: each slide is the layout's background with every slot's content
placed in the template's own box. HTML-to-PDF converters flow content through
frames and cannot pin a slot to a position, which is the whole of a slide.

While drawing, each slot's content is shrunk until it fits, down to a floor
that stays readable; past that it is cut and reported (`MAT-X02`). That is the
one place a slide's real fit can be measured, so the exporter doubles as the
overflow check.

A long-form document is rendered by `xhtml2pdf` from its own HTML with a print
stylesheet, embedding the same fonts as `assessment render`.
"""

from __future__ import annotations

import html as _html
from dataclasses import dataclass, field
from pathlib import Path

from get_fsa_training_done.features.common.render import pdf as pdf_mod

from . import assets, grammar, i18n, rich
from . import deck as deck_mod
from . import layouts as L
from .dom import Document, Element, serialize

THEME = Path(__file__).resolve().parents[1] / "theme"
SANS, SANS_BOLD, MONO = "FsaSans", "FsaSans-Bold", "FsaMono"
#: A body slot's type shrinks no further than this before it is an overflow;
#: a title or text slot follows `layouts.fit_scale` down to its last step.
MIN_SCALE = 0.7
FOOTER = "® Copyright FPT Software - FPT Software Academy - Internal Use"
WITH_FOOTER = {layout.name for layout in L.LAYOUTS if layout.footer}


def _hex(colour: str) -> str:
    return f"#{colour.lower()}"


@dataclass
class Outcome:
    pages: int = 0
    warnings: list[tuple[str, str, str]] = field(default_factory=list)  # (rule, where, message)


def _fonts() -> None:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    registered = set(pdfmetrics.getRegisteredFontNames())
    for name, file in (
        (SANS, "DejaVuSans.ttf"),
        (SANS_BOLD, "DejaVuSans-Bold.ttf"),
        (MONO, "RobotoMono-Regular.ttf"),
        ("FsaMono-Bold", "RobotoMono-Bold.ttf"),
    ):
        if name not in registered:
            pdfmetrics.registerFont(TTFont(name, str(pdf_mod.FONT_DIR / file)))
    from reportlab.lib.fonts import addMapping

    addMapping(SANS, 0, 0, SANS)
    addMapping(SANS, 1, 0, SANS_BOLD)
    addMapping(SANS, 0, 1, SANS)
    addMapping(SANS, 1, 1, SANS_BOLD)
    addMapping(MONO, 0, 0, MONO)
    addMapping(MONO, 1, 0, "FsaMono-Bold")


# --- A deck -----------------------------------------------------------------


def export_deck(document: Document, out: Path) -> Outcome:
    from reportlab.pdfgen import canvas

    _fonts()
    width, height = L.SLIDE_WIDTH_PT, L.SLIDE_HEIGHT_PT
    slides = deck_mod.read(document)
    titles = deck_mod.section_titles(slides)
    outcome = Outcome()
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(out), pagesize=(width, height))
    pdf.setTitle(document.title)
    section = 0

    for slide in slides:
        if slide.layout is None:
            outcome.warnings.append(("MAT-S02", slide.where(), "unknown layout; slide skipped"))
            continue
        layout = slide.layout
        _background(pdf, layout, width, height)
        if layout.role == L.SECTION:
            section += 1
        for spec in layout.slots:
            element = slide.slots.get(spec.name)
            if element is None:
                if spec.default:
                    words = i18n.t(document.lang, spec.default)
                    content = [rich.Block("para", runs=[rich.Run(words)])]
                else:
                    continue
            else:
                content = rich.blocks(element)
                if spec.name == "title" and layout.role == L.SECTION:
                    content = [
                        rich.Block(
                            "para",
                            runs=[rich.Run(f"{section:02d}.\n" + element.text(keep_breaks=True))],
                        )
                    ]
            for block in content:
                if block.kind == "image":
                    _, problem = assets.embeddable(document.path, block.src)
                    if problem:
                        outcome.warnings.append(
                            ("MAT-X03", slide.where(), f"{problem}; image skipped")
                        )
            if layout.name == "cover" and spec.name == "date":
                _date_box(pdf, spec.box, width, height)
            fitted = _draw_slot(pdf, spec, content, document, width, height)
            if not fitted:
                outcome.warnings.append(
                    (
                        "MAT-X02",
                        slide.where(),
                        f"slot {spec.name!r} does not fit even at {MIN_SCALE:.0%} size; cut",
                    )
                )
        if layout.role == L.TOC:
            _toc(pdf, titles, width, height)
        if layout.name in WITH_FOOTER:
            _footer(pdf, slide.number, width, height)
        pdf.showPage()
        outcome.pages += 1

    pdf.save()
    return outcome


def _background(pdf, layout: L.Layout, width: float, height: float) -> None:
    image = THEME / "img" / f"{layout.background}.jpg"
    box = layout.background_box
    if box is None:
        pdf.drawImage(str(image), 0, 0, width, height)
        _rules(pdf, layout, width, height)
        return
    pdf.setFillColor("#ffffff")
    pdf.rect(0, 0, width, height, stroke=0, fill=1)
    pdf.drawImage(
        str(image),
        box.left / 100 * width,
        height - (box.top + box.height) / 100 * height,
        box.width / 100 * width,
        box.height / 100 * height,
        preserveAspectRatio=True,
        anchor="c",
    )


def _rules(pdf, layout: L.Layout, width: float, height: float) -> None:
    pdf.setStrokeColor(_hex(L.RULE_COLOUR))
    pdf.setLineWidth(L.RULE_WIDTH_PT)
    for rule in layout.rules:
        x = rule.left / 100 * width
        y = height - rule.top / 100 * height
        pdf.line(x, y, x + rule.width_pt, y - rule.height_pt)


def _date_box(pdf, box: L.Box, width: float, height: float) -> None:
    """The cover's date sits in the template's translucent rounded box."""
    from reportlab.lib.colors import Color

    x, y = box.left / 100 * width, height - (box.top + box.height) / 100 * height
    pdf.setFillColor(Color(91 / 255, 212 / 255, 1, alpha=0.2))
    pdf.setStrokeColor("#5bd4ff")
    pdf.setLineWidth(0.75)
    pdf.roundRect(x, y, box.width_pt, box.height_pt, 4.5, stroke=1, fill=1)


def _footer(pdf, number: int, width: float, height: float) -> None:
    pdf.setFont(SANS, 7)
    pdf.setFillColor("#a6a6a6")
    pdf.drawString(0.046 * width, 0.026 * height, FOOTER)
    pdf.drawRightString(0.956 * width, 0.026 * height, str(number))


def _toc(pdf, titles: list[str], width: float, height: float) -> None:
    """A green circle with a white ring and the title beside it, per row."""
    for row, (title, ((_, number), (_, label))) in enumerate(zip(titles, L.TOC_ROWS, strict=False)):
        cx = (number.left + number.width / 2) / 100 * width
        cy = height - (number.top + number.height / 2) / 100 * height
        radius = min(number.width_pt, number.height_pt) / 2 - 1.1
        pdf.setFillColor("#50b748")
        pdf.setStrokeColor("#ffffff")
        pdf.setLineWidth(2.25)
        pdf.circle(cx, cy, radius, stroke=1, fill=1)
        pdf.setFillColor("#ffffff")
        pdf.setFont(SANS, L.TOC_SIZE)
        pdf.drawCentredString(cx, cy - L.TOC_SIZE * 0.35, str(row + 1))
        ly = height - (label.top + label.height / 2) / 100 * height
        pdf.drawString(label.left / 100 * width + L.INSET_X, ly - L.TOC_SIZE * 0.35, title)


def _escape(text: str) -> str:
    return _html.escape(text, quote=False)


def _markup(runs: list[rich.Run], colour: str, bold_all: bool) -> str:
    parts = []
    for run in runs:
        text = _escape(run.text).replace("\n", "<br/>")
        if run.code:
            text = f'<font face="{MONO}">{text}</font>'
        if run.bold or bold_all:
            text = f"<b>{text}</b>"
            if run.bold and colour == _hex(L.BLACK):
                text = f'<font color="#034ea1">{text}</font>'
        if run.italic:
            text = f"<i>{text}</i>"
        if run.href:
            text = f'<a href="{_escape(run.href)}" color="{colour}">{text}</a>'
        parts.append(text)
    return "".join(parts)


#: How far a line may be condensed to keep the browser's line count.
MIN_CONDENSE = 0.8


def _draw_fitted_lines(pdf, spec: L.Slot, text: str, x, top, avail_w, avail_h) -> bool:
    """Draw a title or text slot line for line as the browser does, if it can.

    When the shared estimate puts the text on its own lines with no wrapping,
    each line is drawn at the estimate's size and condensed just enough to fit:
    the PDF's embedded face runs wider than Arial, and without this a title the
    browser shows on one line wraps onto two here.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return True
    scale = L.fit_scale(spec, text)
    size = spec.size * scale
    if L.lines_needed(text, avail_w, size, spec.bold) != len(lines):
        return False
    font = SANS_BOLD if spec.bold else SANS
    widths = [stringWidth(line, font, size) for line in lines]
    condense = min(1.0, avail_w / max(widths))
    if condense < MIN_CONDENSE:
        return False
    leading = size * L.LINE_HEIGHT
    block = leading * len(lines)
    offset = {"top": 0.0, "middle": (avail_h - block) / 2, "bottom": avail_h - block}[spec.anchor]
    pdf.setFillColor(_hex(spec.colour))
    y = top - offset - size * 0.93
    for line, width in zip(lines, widths, strict=True):
        drawn = width * condense
        start = x + (avail_w - drawn) / 2 if spec.align == "center" else x
        text_object = pdf.beginText()
        text_object.setFont(font, size)
        text_object.setHorizScale(condense * 100)
        text_object.setTextOrigin(start, y)
        text_object.textLine(line)
        pdf.drawText(text_object)
        y -= leading
    return True


def _text_height(spec: L.Slot, content, scale: float) -> float:
    """A rough height for a slot's non-picture blocks, to size its picture by."""
    base = (spec.size or 18) * scale
    total = 0.0
    for block in content:
        if block.kind == "caption":
            total += base * 0.55 * L.LINE_HEIGHT + 4
        elif block.kind in ("code", "diagram"):
            total += len(block.lines) * min(base * 0.62, 14 * scale) * 1.35 + 12
        elif block.kind not in ("image", "table"):
            total += base * L.LINE_HEIGHT * 1.3
    return total


def _flowables(
    spec: L.Slot, content, document: Document, scale: float, avail_w: float, avail_h: float
):
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Image, Paragraph, Preformatted, Spacer, Table, TableStyle

    colour = _hex(spec.colour)
    base = (spec.size or 18) * scale
    items = []
    number = 0
    for block in content:
        size = base * (0.82**block.level)
        if block.kind in ("code", "diagram"):
            code_size = L.code_size(spec) * scale
            style = ParagraphStyle(
                "code",
                fontName=MONO,
                fontSize=code_size,
                leading=code_size * 1.35,
                backColor="#f2f5fa" if spec.colour == L.BLACK else None,
                borderPadding=(4, 6, 4, 6),
                textColor="#1f2328" if spec.colour == L.BLACK else colour,
            )
            if block.label:
                label = (
                    f"✗ {i18n.t(document.lang, 'Wrong')}"
                    if block.label == "wrong"
                    else f"✓ {i18n.t(document.lang, 'Right')}"
                )
                tint = "#c62828" if block.label == "wrong" else "#2e7d32"
                items.append(
                    Paragraph(
                        f"<b>{label}</b>",
                        ParagraphStyle("label", fontName=SANS, fontSize=code_size, textColor=tint),
                    )
                )
            items.append(Spacer(1, 3))
            items.append(Preformatted("\n".join(block.lines), style))
            items.append(Spacer(1, 6))
            continue
        if block.kind == "image":
            path, _ = assets.embeddable(document.path, block.src)
            if path is not None:
                image = Image(str(path))
                ratio = image.imageWidth / image.imageHeight
                # As in the browser and the .pptx: the picture fits the room the
                # slot's text leaves it, keeping its proportions.
                room = avail_h - _text_height(spec, content, scale)
                image.drawHeight = max(room, avail_h * 0.3)
                image.drawWidth = image.drawHeight * ratio
                if image.drawWidth > avail_w:
                    image.drawWidth = avail_w
                    image.drawHeight = avail_w / ratio
                items.append(image)
            continue
        if block.kind == "caption":
            items.append(
                Paragraph(
                    _escape(block.text()),
                    ParagraphStyle(
                        "caption",
                        fontName=SANS,
                        fontSize=base * 0.55,
                        leading=base * 0.55 * L.LINE_HEIGHT,
                        textColor="#5b6370",
                        alignment=1,
                        spaceBefore=4,
                    ),
                )
            )
            continue
        if block.kind == "table":
            cell = ParagraphStyle("cell", fontName=SANS, fontSize=base * 0.7, leading=base * 0.85)
            head = ParagraphStyle("head", parent=cell, textColor="#ffffff", fontName=SANS_BOLD)
            data = [
                [
                    Paragraph(_escape(text), head if (r == 0 and block.header) else cell)
                    for text in row
                ]
                for r, row in enumerate(block.rows)
            ]
            if data:
                table = Table(
                    data,
                    colWidths=[avail_w / max(len(r) for r in data)] * max(len(r) for r in data),
                )
                commands = [("GRID", (0, 0), (-1, -1), 0.5, "#d3dbe8")]
                if block.header:
                    commands.append(("BACKGROUND", (0, 0), (-1, 0), "#034ea1"))
                table.setStyle(TableStyle(commands))
                table.spaceBefore, table.spaceAfter = base * 0.15, base * 0.3
                items.append(table)
            continue
        indent = 14 * scale
        style = ParagraphStyle(
            "p",
            fontName=SANS,
            fontSize=size,
            leading=size * L.LINE_HEIGHT,
            textColor=colour,
            spaceAfter=size * 0.3,
            leftIndent=indent * (block.level + (1 if block.kind != "para" else 0)),
            bulletIndent=indent * block.level,
            alignment={"left": 0, "center": 1}.get(spec.align, 0),
        )
        bullet = None
        if block.kind == "bullet":
            bullet = "•"
            style.bulletColor = (
                colour if colour == "#ffffff" else ("#50b748" if block.level == 0 else "#034ea1")
            )
        elif block.kind == "number":
            number += 1
            bullet = f"{number}."
            style.bulletColor = colour
        style.bulletFontName = SANS
        style.bulletFontSize = size
        items.append(
            Paragraph(
                _markup(block.runs, colour, spec.bold),
                style,
                bulletText=bullet,
            )
        )
    return items


def _room(spec: L.Slot, width, height) -> tuple[float, float]:
    """The width and height a slot's content has inside its insets."""
    return (
        spec.box.width / 100 * width - 2 * L.INSET_X,
        spec.box.height / 100 * height - 2 * L.INSET_Y,
    )


def _fit(spec: L.Slot, content, document: Document, scales, avail_w, avail_h):
    """The first of `scales` at which a body's content fits: its flowables, their
    sizes, the height they take, and whether they fit at all."""
    items, sizes, used = [], [], 0.0
    for scale in scales:
        items = _flowables(spec, content, document, scale, avail_w, avail_h)
        sizes = [item.wrap(avail_w, avail_h) for item in items]
        used = sum(h + _gap(item) for item, (_, h) in zip(items, sizes, strict=True))
        if used <= avail_h:
            return items, sizes, used, True
    return items, sizes, used, False


def _gap(item) -> float:
    """The space a flowable asks for around itself. `wrap` leaves it out, and
    without it a paragraph's last line runs under the table that follows."""
    return item.getSpaceBefore() + item.getSpaceAfter()


#: The white content layouts, where an unfilled body is empty slide. The card,
#: column and row layouts are drawn full by the template, and a picture fills
#: what its body leaves.
FILLABLE = frozenset({"content", "two-content", "three-content", "subtitle-content", "title-only"})


def fill(slide: deck_mod.Slide, document: Document) -> float | None:
    """How much of a content slide's body room its content takes, laid out as
    `export pdf` draws it: 0.4 is a slide whose lower half and more is blank.
    None for a slide whose layout is not one of `FILLABLE`."""
    layout = slide.layout
    if layout is None or layout.name not in FILLABLE:
        return None
    _fonts()
    width, height = L.SLIDE_WIDTH_PT, L.SLIDE_HEIGHT_PT
    scales = [scale for scale in L.FIT_SCALES if scale >= MIN_SCALE]
    used_total = room_total = 0.0
    for spec in layout.slots:
        if spec.kind != L.BODY:
            continue
        avail_w, avail_h = _room(spec, width, height)
        room_total += avail_h
        element = slide.slots.get(spec.name)
        if element is None:
            continue
        _, _, used, _ = _fit(spec, rich.blocks(element), document, scales, avail_w, avail_h)
        used_total += min(used, avail_h)
    return used_total / room_total if room_total else None


def _draw_slot(pdf, spec: L.Slot, content, document: Document, width, height) -> bool:
    x = spec.box.left / 100 * width + L.INSET_X
    top = height - spec.box.top / 100 * height - L.INSET_Y
    avail_w = spec.box.width / 100 * width - 2 * L.INSET_X
    avail_h = spec.box.height / 100 * height - 2 * L.INSET_Y
    if spec.fits:
        text = "\n".join(block.text() for block in content)
        if _draw_fitted_lines(pdf, spec, text, x, top, avail_w, avail_h):
            return True
        # The same step the browser and PowerPoint pick, then smaller if the PDF's
        # face runs wider than the estimate.
        start = L.fit_scale(spec, text)
        scales = [scale for scale in L.FIT_SCALES if scale <= start]
    else:
        scales = [scale for scale in L.FIT_SCALES if scale >= MIN_SCALE]
    items, sizes, used, fitted = _fit(spec, content, document, scales, avail_w, avail_h)
    offset = 0.0
    if fitted and spec.anchor == "middle":
        offset = (avail_h - used) / 2
    elif fitted and spec.anchor == "bottom":
        offset = avail_h - used
    y = top - offset
    floor = top - avail_h
    for item, (w, h) in zip(items, sizes, strict=True):
        # A title or text slot is drawn whole, running past its box as it does in
        # the browser and in PowerPoint; a body is cut where its box ends.
        y -= item.getSpaceBefore()
        if not fitted and not spec.fits and y - h < floor:
            break
        x_item = (
            x + (avail_w - w) / 2 if spec.align == "center" or hasattr(item, "imageWidth") else x
        )
        item.drawOn(pdf, x_item, y - h)
        y -= h + item.getSpaceAfter()
    return fitted or spec.fits


# --- A long-form document ---------------------------------------------------

#: The printed page as `PRINT_CSS` sets it: A4, 16mm side margins, code in
#: Roboto Mono at 8.5pt (0.6em a character) inside 6pt padding and a 3pt rule;
#: each list or quote it sits in indents it about 24pt more.
A4_WIDTH_PT = 595.28
SIDE_MARGIN_PT = 16 / 25.4 * 72
CODE_PT, CODE_PADDING_PT, NESTED_INDENT_PT = 8.5, 6 * 2 + 3, 24


def doc_code_columns(depth: int = 0) -> int:
    """How many characters of a code line fit the printed page at a nesting depth;
    xhtml2pdf neither wraps nor shrinks a `<pre>`, so the rest is cut."""
    room = A4_WIDTH_PT - 2 * SIDE_MARGIN_PT - CODE_PADDING_PT - NESTED_INDENT_PT * depth
    return int(room // (CODE_PT * 0.6))


FONT_CSS = """
@font-face { font-family: "FsaSans"; src: url("DejaVuSans.ttf"); }
@font-face { font-family: "FsaSans"; src: url("DejaVuSans-Bold.ttf"); font-weight: bold; }
@font-face { font-family: "FsaMono"; src: url("RobotoMono-Regular.ttf"); }
@font-face { font-family: "FsaMono"; src: url("RobotoMono-Bold.ttf"); font-weight: bold; }
"""

PRINT_CSS = """
@page { size: A4; margin: 20mm 16mm 20mm 16mm;
  @frame footer { -pdf-frame-content: page-footer; bottom: 8mm; margin-left: 16mm;
    margin-right: 16mm; height: 8mm; } }
body { font-family: FsaSans; font-size: 10.5pt; line-height: 1.45; color: #1f2328; }
h1 { font-size: 20pt; color: #034ea1; margin: 0 0 2pt 0; }
.meta { color: #5b6370; font-size: 9pt; border-bottom: 2pt solid #50b748;
  padding-bottom: 6pt; margin-bottom: 12pt; }
h2 { font-size: 14pt; color: #034ea1; margin: 14pt 0 4pt 0; -pdf-keep-with-next: true; }
h3 { font-size: 11.5pt; margin: 10pt 0 3pt 0; -pdf-keep-with-next: true; }
p { margin: 0 0 6pt 0; }
li { margin: 0 0 3pt 0; }
li.numbered { list-style-type: none; }
dt { font-weight: bold; margin: 4pt 0 0 0; }
dd { margin: 0 0 4pt 12pt; }
code { font-family: FsaMono; font-size: 9pt; background-color: #f2f5fa; }
pre { font-family: FsaMono; font-size: 8.5pt; background-color: #f2f5fa;
  border-left: 3pt solid #034ea1; padding: 6pt; margin: 4pt 0 8pt 0; }
table { border: 0.5pt solid #d8dee8; margin: 4pt 0 8pt 0; }
th { background-color: #034ea1; color: #ffffff; padding: 3pt; text-align: left; }
td { padding: 3pt; border: 0.5pt solid #d8dee8; }
td code, th code { -pdf-word-wrap: CJK; }
figure { display: block; margin: 6pt 0 10pt 0; text-align: center; }
figure img { display: block; }
figcaption { display: block; font-size: 9pt; color: #5b6370; margin-top: 3pt; }
.try-it { border: 1.5pt solid #50b748; padding: 6pt; margin: 6pt 0 10pt 0; }
.callout { border-left: 3pt solid #034ea1; background-color: #f3f6fb; padding: 6pt; }
.answer { color: #2e5d2a; background-color: #f3f6fb; padding: 4pt; margin: 2pt 0 6pt 0; }
.answer-label { font-weight: bold; color: #50b748; }
.expected { border-left: 3pt solid #50b748; background-color: #f3f6fb; padding: 4pt; }
.code-tag { color: #ffffff; background-color: #034ea1; font-size: 7.5pt; }
.code-wrong { color: #c62828; font-weight: bold; font-size: 8pt; margin: 6pt 0 0 0; }
.code-right { color: #2e7d32; font-weight: bold; font-size: 8pt; margin: 6pt 0 0 0; }
.xref-file { color: #5b6370; font-size: 8pt; -pdf-word-wrap: CJK; }
p.xref-file { margin: 0; }
.page-footer { color: #9aa3b2; font-size: 7.5pt; }
"""

_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}


def _node(tag: str, text: str = "", **attrs: str) -> Element:
    element = Element(tag, {key.rstrip("_"): value for key, value in attrs.items()}, 0)
    if text:
        element.children.append(text)
    return element


def _replace(old: Element, new: list[Element | str]) -> None:
    siblings = old.parent.children
    index = next(i for i, child in enumerate(siblings) if child is old)
    siblings[index : index + 1] = new
    for child in new:
        if isinstance(child, Element):
            child.parent = old.parent


def _pdf_name(target: str) -> str:
    """The file a link to a sibling points at once the module is exported:
    `01_Topic.deck.html` → `01_Topic.deck.pdf`, `dbf_lab_01.html` → `dbf_lab_01.pdf`."""
    return target[: -len(".html")] + ".pdf" if target.endswith(".html") else target


def _links(body: Element) -> None:
    """Make the document's links work in a PDF.

    xhtml2pdf jumps only to `<a name>`, never to an `id`, so every id gets one —
    at the start of a part's heading, where the reader should land. And it
    keeps only a link to `#…` or to a URL with a scheme: a link to a file beside
    the document is dropped, and a PDF cannot open its sibling reliably anyway.
    Such a link keeps its words and names the PDF to open instead.
    """
    for element in list(body.iter()):
        anchor = element.get("id")
        if not anchor or element.tag == "a":
            continue
        heading = element.find("h2") if element.tag == "section" else None
        target = heading if heading is not None else element
        target.children.insert(0, _node("a", name=anchor))

    for link in body.find_all("a"):
        href = link.get("href")
        if not href or href.startswith("#") or assets.is_external(href):
            continue
        target, _ = assets.split(href)
        if not target:
            continue
        name = _pdf_name(target.rsplit("/", 1)[-1])
        span = _node("span", class_="xref")
        # In a table cell a file name has no room beside the words: it goes on
        # its own line, where it may wrap at any letter rather than run into
        # the next column.
        if link.ancestor("td") is not None or link.ancestor("th") is not None:
            file = _node("p", name, class_="xref-file")
        else:
            file = _node("span", f"({name})", class_="xref-file")
        span.children.extend([*link.children, " ", file])
        for child in span.children:
            if isinstance(child, Element):
                child.parent = span
        _replace(link, [span])


def _prepare(document: Document, warnings: list) -> Element:
    """The document's body, rewritten for a renderer with no script and little CSS.

    Everything the browser gets from the theme and doc.js is written out:
    numbered part headings, Wrong/Right labels, each objective's code after
    its text, answers shown rather than folded, images inlined, and the source
    of a diagram that has its picture dropped.
    """
    import base64

    lang = document.lang
    body = document.body
    for script in body.find_all("script"):
        _replace(script, [])

    for figure in body.find_all("figure"):
        if figure.find("img") is not None:
            for pre in figure.find_all("pre"):
                if "mermaid" in pre.classes:
                    _replace(pre, [])

    for image in body.find_all("img"):
        src = image.get("src")
        if src.startswith("data:"):
            continue
        path, problem = assets.embeddable(document.path, src)
        if path is None:
            warnings.append(("MAT-X03", src or "<img>", f"{problem}; image skipped"))
            _replace(image, [])
            continue
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        image.attrs["src"] = f"data:{_MIME[path.suffix.lower()]};base64,{data}"

    number = 0
    for section in body.find_all("section"):
        heading = section.find("h2")
        if section.get("data-part") and heading is not None:
            number += 1
            heading.children.insert(0, f"{number}. ")

    _links(body)

    for pre in body.find_all("pre"):
        for kind in ("wrong", "right"):
            if kind in pre.classes:
                mark = "✗" if kind == "wrong" else "✓"
                label = _node(
                    "p", f"{mark} {i18n.t(lang, kind.title()).upper()}", class_=f"code-{kind}"
                )
                _replace(pre, [label, pre])

    for item in body.find_all():
        code = item.get("data-objective")
        if code and item.tag in ("li", "p"):
            tag = _node("span", f"\u00a0{code}\u00a0", class_="code-tag")
            details = item.find("details")
            if details is not None and details.parent is item:
                index = next(i for i, child in enumerate(item.children) if child is details)
                # Inside the question's own paragraph: beside it, the tag is a
                # block of its own and prints as a bar across the page.
                question = next(
                    (
                        child
                        for child in reversed(item.children[:index])
                        if isinstance(child, Element) and child.tag == "p"
                    ),
                    None,
                )
                if question is not None:
                    question.children.extend([" ", tag])
                else:
                    item.children[index:index] = [" ", tag]
            else:
                item.children.extend([" ", tag])

    # xhtml2pdf drops an item's number when the item opens with a paragraph — a
    # review question, a lab step. Every ordered list's numbers are written out,
    # and the renderer's own hidden, so one list never mixes the two.
    for ordered in body.find_all("ol"):
        start = ordered.get("start")
        first_number = int(start) if start.isdigit() else 1
        items = [child for child in ordered.elements if child.tag == "li"]
        for position, item in enumerate(items, first_number):
            lead = next(
                (
                    child
                    for child in item.children
                    if not (isinstance(child, str) and not child.strip())
                ),
                None,
            )
            holder = lead if isinstance(lead, Element) and lead.tag == "p" else item
            holder.children.insert(0, f"{position}. ")
            item.attrs["class"] = " ".join(filter(None, (item.get("class"), "numbered")))

    for details in body.find_all("details"):
        summary = details.find("summary")
        label = summary.text() if summary is not None else i18n.t(lang, "Answer")
        answer = _node("div", class_="answer")
        answer.children.append(_node("span", f"{label}. ", class_="answer-label"))
        for child in details.children:
            if child is summary:
                continue
            if isinstance(child, Element) and child.tag == "p":
                answer.children.extend(child.children + [" "])
            else:
                answer.children.append(child)
        _replace(details, [answer])
    return body


def _print_html(document: Document, warnings: list | None = None) -> str:
    lang = document.lang
    body = _prepare(document, warnings if warnings is not None else [])
    facts = [
        document.meta(grammar.META_MODULE),
        f"{i18n.t(lang, 'Session')} {document.meta(grammar.META_SESSION)}"
        if document.meta(grammar.META_SESSION)
        else "",
        f"{document.meta(grammar.META_MINUTES)} {i18n.t(lang, 'min')}"
        if document.meta(grammar.META_MINUTES)
        else "",
        document.meta(grammar.META_STACK),
    ]
    meta = " · ".join(fact for fact in facts if fact)
    title = body.find("h1")
    if meta and title is not None:
        _replace(title, [title, _node("p", meta, class_="meta")])
    inner = "".join(serialize(child) for child in body.children)
    footer = f'<div id="page-footer" class="page-footer">{_escape(document.title)} — {FOOTER}</div>'
    return (
        f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
        f"<title>{_escape(document.title)}</title>"
        f"<style>{FONT_CSS}{PRINT_CSS}</style></head><body>{footer}{inner}</body></html>"
    )


def export_document(document: Document, out: Path) -> Outcome:
    out.parent.mkdir(parents=True, exist_ok=True)
    warnings: list[tuple[str, str, str]] = []
    pages = pdf_mod.render_html(_print_html(document, warnings), out)
    return Outcome(pages=pages or 0, warnings=warnings)


__all__ = ["Outcome", "export_deck", "export_document"]
