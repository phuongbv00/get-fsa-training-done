"""SVG illustrations, made into pictures the exporters can place.

A browser shows an SVG as it is. PowerPoint and the PDF writers place raster
images, so `export` draws each SVG to a PNG first: svglib reads it into a
reportlab drawing, reportlab writes that as a one-page PDF, and pdfium renders
the page. All three are Python packages with wheels — no browser and no
external binary, which is the rule every feature keeps.

The SVG's fonts are the module's: every `font-family` becomes the embedded
DejaVu (or Roboto Mono for a monospace family), so Vietnamese keeps its
diacritics and a diagram reads the same on every machine.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "{http://www.w3.org/2000/svg}"

#: What svglib cannot draw: the export would show the SVG without it, so an
#: arrowhead or a shadow silently disappears from the slide handed out.
UNSUPPORTED = {
    "marker": "an arrowhead drawn with <marker>; draw it as a <polygon> or <path>",
    "filter": "a <filter> (shadow, blur)",
    "mask": "a <mask>",
    "foreignObject": "a <foreignObject> (HTML inside the SVG)",
    "pattern": "a <pattern> fill",
    "textPath": "text along a <textPath>",
}
MARKER_ATTRIBUTES = ("marker-start", "marker-mid", "marker-end")

#: How much larger than its own size the PNG is drawn: sharp on a projector.
SCALE = 3

FONT_FAMILY_ATTR = re.compile(r'font-family\s*=\s*("[^"]*"|\'[^\']*\')')
FONT_FAMILY_CSS = re.compile(r"font-family\s*:\s*([^;\"'}]+|\"[^\"]*\"|'[^']*')")
MONOSPACE = re.compile(r"mono|courier|consol|menlo", re.IGNORECASE)


def _family(value: str) -> str:
    from .export_pdf import MONO, SANS

    return MONO if MONOSPACE.search(value) else SANS


def normalise_fonts(text: str) -> str:
    """Every font family the SVG names, as one of the module's embedded fonts."""
    text = FONT_FAMILY_ATTR.sub(lambda m: f'font-family="{_family(m.group(1))}"', text)
    text = FONT_FAMILY_CSS.sub(lambda m: f"font-family: {_family(m.group(1))}", text)
    # Text with no family of its own inherits the root's.
    if not FONT_FAMILY_ATTR.search(text.split(">", 1)[0] + ">"):
        from .export_pdf import SANS

        text = re.sub(r"<svg\b", f'<svg font-family="{SANS}"', text, count=1)
    return text


def unsupported(path: Path) -> list[str]:
    """What in the SVG the exporters would drop, one entry per kind."""
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        return [f"it cannot be read: {exc}"]
    found: dict[str, str] = {}
    for element in root.iter():
        tag = element.tag.removeprefix(SVG_NS) if isinstance(element.tag, str) else ""
        if tag in UNSUPPORTED:
            found.setdefault(tag, UNSUPPORTED[tag])
        if any(element.get(name) for name in MARKER_ATTRIBUTES):
            found.setdefault("marker", UNSUPPORTED["marker"])
    return list(found.values())


def _cache() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or tempfile.gettempdir()
    folder = Path(base) / "get-fsa-training-done" / "svg"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def to_png(path: Path) -> Path:
    """The PNG of an SVG, drawn once per version of the file and kept in a cache.

    Raises `ValueError` when the SVG cannot be drawn.
    """
    source = path.read_bytes()
    digest = hashlib.sha256(source + f"x{SCALE}".encode()).hexdigest()[:20]
    out = _cache() / f"{path.stem}-{digest}.png"
    if out.is_file():
        return out

    import pypdfium2
    from reportlab.graphics import renderPDF
    from svglib.svglib import svg2rlg

    from .export_pdf import _fonts

    _fonts()
    _register_svg_fonts()
    text = normalise_fonts(source.decode("utf-8"))
    drawing = svg2rlg(io.BytesIO(text.encode("utf-8")))
    if drawing is None or not drawing.width or not drawing.height:
        raise ValueError(f"{path.name} has nothing to draw")
    pdf = renderPDF.drawToString(drawing)
    document = pypdfium2.PdfDocument(pdf)
    try:
        image = document[0].render(scale=SCALE).to_pil()
    finally:
        document.close()
    tmp = out.with_suffix(".tmp")
    image.save(tmp, format="PNG")
    tmp.replace(out)
    return out


def _register_svg_fonts() -> None:
    """svglib keeps its own font map: tell it the module's fonts are there."""
    from svglib import fonts

    from get_fsa_training_done.features.common.render import pdf as pdf_mod

    from . import export_pdf

    for family, weight, file, name in (
        (export_pdf.SANS, "normal", "DejaVuSans.ttf", export_pdf.SANS),
        (export_pdf.SANS, "bold", "DejaVuSans-Bold.ttf", export_pdf.SANS_BOLD),
        (export_pdf.MONO, "normal", "RobotoMono-Regular.ttf", export_pdf.MONO),
        (export_pdf.MONO, "bold", "RobotoMono-Bold.ttf", "FsaMono-Bold"),
    ):
        fonts.register_font(family, str(pdf_mod.FONT_DIR / file), weight=weight, rlgFontName=name)


__all__ = ["UNSUPPORTED", "normalise_fonts", "to_png", "unsupported"]
