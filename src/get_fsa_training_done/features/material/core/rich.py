"""A slot's content as blocks of styled runs, for the two exporters.

PowerPoint and the PDF writer cannot read HTML, but they can draw paragraphs,
list items, code lines, a picture and a table. This is the one translation from
the deck's dialect to those; `export_pptx` and `export_pdf` each draw the result
their own way, so the two files always agree on what a slide says.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .dom import Element

INLINE_BOLD = ("strong", "b")
INLINE_ITALIC = ("em", "i")
#: Elements that start a block of their own; everything else is inline and
#: flows into the paragraph around it.
BLOCK = frozenset(
    "p h1 h2 h3 h4 h5 h6 ul ol li pre figure figcaption table img div section blockquote "
    "details summary aside dl dt dd hr".split()
)
#: Blocks that are paragraphs of text.
PARAGRAPHS = frozenset("p h3 h4 h5 h6 figcaption summary dt dd".split())


@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    href: str = ""


@dataclass
class Block:
    #: para | bullet | number | code | image | table | diagram | caption
    kind: str
    level: int = 0
    runs: list[Run] = field(default_factory=list)
    #: `code` and `diagram`: the lines as written.
    lines: list[str] = field(default_factory=list)
    #: `image`: the file, relative to the deck, and what it shows.
    src: str = ""
    alt: str = ""
    #: `table`: rows of cell text; the first is a header when `header`.
    rows: list[list[str]] = field(default_factory=list)
    header: bool = False
    #: `code`: a `wrong` / `right` label from the `<pre>`'s class.
    label: str = ""

    def text(self) -> str:
        return "".join(run.text for run in self.runs)


def runs_of(element: Element, *, bold=False, italic=False, code=False, href="") -> list[Run]:
    """Inline content, flattened. Blocks — paragraphs, lists, code, pictures — are
    left out: they are walked as blocks of their own."""
    found: list[Run] = []
    for child in element.children:
        if isinstance(child, str):
            text = " ".join(child.split()) if not code else child
            if child[:1].isspace() and text:
                text = " " + text
            if child[-1:].isspace() and text and not text.endswith(" "):
                text += " "
            if text:
                found.append(Run(text, bold, italic, code, href))
            continue
        tag = child.tag
        if tag in BLOCK:
            continue
        if tag == "br":
            found.append(Run("\n", bold, italic, code, href))
            continue
        found.extend(
            runs_of(
                child,
                bold=bold or tag in INLINE_BOLD,
                italic=italic or tag in INLINE_ITALIC,
                code=code or tag == "code",
                href=child.get("href") if tag == "a" else href,
            )
        )
    return _tidy(found)


def _tidy(runs: list[Run]) -> list[Run]:
    """Collapse the whitespace between runs the way a browser would."""
    out: list[Run] = []
    for run in runs:
        if out and out[-1].text.endswith((" ", "\n")) and run.text.startswith(" "):
            run = Run(run.text.lstrip(" "), run.bold, run.italic, run.code, run.href)
        if run.text:
            out.append(run)
    if out:
        out[0].text = out[0].text.lstrip()
        out[-1].text = out[-1].text.rstrip()
    return [run for run in out if run.text]


def blocks(element: Element) -> list[Block]:
    """Every block in a slot, in reading order. A slot may itself be the block:
    a picture slot written as `<img data-slot="picture">`."""
    if element.tag == "img":
        return [Block("image", src=element.get("src"), alt=element.get("alt"))]
    if element.tag in PARAGRAPHS or element.tag in ("h1", "h2"):
        found: list[Block] = []
        runs = runs_of(element)
        if runs:
            found.append(Block("para", runs=runs))
        _walk(element, found, level=0, inline=False)
        return found
    found = []
    _walk(element, found, level=0)
    return found


def _walk(element: Element, found: list[Block], level: int, *, inline: bool = True) -> None:
    """Blocks in order; runs of inline content between them become paragraphs.

    With `inline` off, the element's own inline content has been taken already
    (a list item's text, a heading slot's) and only its blocks are walked.
    """
    pending: list[Element | str] = []

    def flush() -> None:
        if inline and pending:
            runs = runs_of(Element("span", {}, element.line, children=list(pending)))
            if runs:
                found.append(Block("para", level=level, runs=runs))
        pending.clear()

    for child in element.children:
        if isinstance(child, str) or child.tag not in BLOCK:
            pending.append(child)
            continue
        flush()
        tag = child.tag
        if tag in PARAGRAPHS:
            runs = runs_of(child)
            if runs:
                found.append(Block("para", level=level, runs=runs))
        elif tag in ("ul", "ol"):
            kind = "number" if tag == "ol" else "bullet"
            for item in child.elements:
                if item.tag == "li":
                    _item(item, kind, found, level)
        elif tag == "pre":
            lines = child.raw_text().strip("\n").splitlines()
            if "mermaid" in child.classes:
                found.append(Block("diagram", lines=lines))
            else:
                label = (
                    "wrong"
                    if "wrong" in child.classes
                    else ("right" if "right" in child.classes else "")
                )
                found.append(Block("code", lines=lines, label=label))
        elif tag == "figure":
            image = child.find("img")
            if image is not None:
                found.append(Block("image", src=image.get("src"), alt=image.get("alt")))
            else:
                diagram = child.find("pre")
                if diagram is not None:
                    found.append(
                        Block("diagram", lines=diagram.raw_text().strip("\n").splitlines())
                    )
            caption = child.find("figcaption")
            if caption is not None and caption.text():
                found.append(Block("caption", runs=[Run(caption.text())]))
        elif tag == "img":
            found.append(Block("image", src=child.get("src"), alt=child.get("alt")))
        elif tag == "table":
            found.append(_table(child))
        elif tag in ("div", "section", "blockquote", "dl"):
            _walk(child, found, level)
        # details, aside, hr and headings above h3 carry nothing for a slide.
    flush()


def _item(item: Element, kind: str, found: list[Block], level: int) -> None:
    """A list item: its text as the bullet, its blocks nested a level deeper.

    `<li><p>text</p>…</li>` is common; the first paragraph is then the bullet's
    text rather than a second copy of it.
    """
    runs = runs_of(item)
    rest = item
    if not runs:
        first = next((child for child in item.elements if child.tag in BLOCK), None)
        if first is not None and first.tag == "p":
            runs = runs_of(first)
            rest = Element(
                "div", {}, item.line, children=[c for c in item.children if c is not first]
            )
    if runs:
        found.append(Block(kind, level=level, runs=runs))
    _walk(rest, found, level + 1, inline=False)


def _table(element: Element) -> Block:
    rows = []
    header = False
    for index, row in enumerate(element.find_all("tr")):
        cells = [cell for cell in row.elements if cell.tag in ("th", "td")]
        if index == 0 and cells and all(cell.tag == "th" for cell in cells):
            header = True
        rows.append([cell.text() for cell in cells])
    return Block("table", rows=rows, header=header)


def answers(element: Element) -> list[str]:
    """What a slide folds into `<details>`: spoken, never shown, on an export."""
    found = []
    for details in element.find_all("details"):
        parts = [
            child.text() for child in details.elements if child.tag != "summary" and child.text()
        ]
        if parts:
            found.append(" ".join(parts))
    return found


def notes_paragraphs(element: Element | None) -> list[str]:
    if element is None:
        return []
    paragraphs = [child.text() for child in element.elements if child.tag in ("p", "li")]
    return [text for text in paragraphs if text] or ([element.text()] if element.text() else [])


__all__ = ["Block", "Run", "answers", "blocks", "notes_paragraphs", "runs_of"]
