"""Rendering a brief to PDF, and counting the pages it made.

The renderer is `xhtml2pdf` running in the managed venv, so `render` needs
nothing installed on the machine. It replaced headless Chrome, which was the one
piece of this toolchain that required a large external binary and which resolved
fonts from whatever the host happened to have — fine for English, quietly wrong
for Vietnamese.

Two consequences worth knowing:

* Fonts are embedded from `core/fonts/` rather than named, so a `_vn` brief
  renders identically everywhere. See that directory's README.
* `xhtml2pdf` implements less print CSS than Chrome — `break-inside` and
  `break-after` are ignored — so pagination differs from PDFs produced before
  the switch. The page *budget* still holds; a given brief may simply land on a
  different number of pages than it used to.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from get_fsa_training_done.errors import GftdError

FONT_DIR = Path(__file__).resolve().parent / "fonts"

#: The faces every brief must carry. Without them the renderer falls back to
#: Helvetica, which has no Vietnamese letters: the PDF still renders, with
#: boxes where the diacritics were.
REQUIRED_FONTS = ("DejaVuSans",)

_BASE_FONT = re.compile(rb"/BaseFont\s*/(?:[A-Z]{6}\+)?([A-Za-z0-9-]+)")
_PAGE_OBJECT = re.compile(rb"/Type\s*/Page(?![s])")
_OBJECT = re.compile(rb"\d+\s+\d+\s+obj\b(.*?)\bendobj", re.DOTALL)
_PAGES_NODE = re.compile(rb"/Type\s*/Pages\b")
_COUNT = re.compile(rb"/Count\s+(\d+)")


def link_callback(uri: str, rel: str = "") -> str:
    """Resolve a document URI to a real path.

    The stylesheet names fonts by bare filename so no filesystem path is baked
    into the CSS — that would have to be quoted differently on Windows. Anything
    that is not one of ours is handed back untouched; the document is otherwise
    self-contained, so there is nothing else to fetch.
    """
    candidate = FONT_DIR / Path(uri).name
    if candidate.is_file():
        return str(candidate)
    return uri


def render_html(document: str, out_pdf: Path) -> int | None:
    """Write `document` to `out_pdf`, returning the page count.

    Raises rather than leaving a half-written file: a PDF that exists but is
    wrong is worse than one that is missing, because the page-budget check would
    then measure it.
    """
    try:
        from xhtml2pdf import pisa
    except ImportError as exc:  # pragma: no cover - the venv guarantees it
        raise GftdError(
            "the PDF renderer is not available in this environment",
            hint="run `gftd install` to build the managed environment",
        ) from exc

    # xhtml2pdf logs every print-CSS property it does not implement. We know
    # which ones those are and have decided to live with them; repeating the
    # list on every render would just train the user to ignore our output.
    logging.getLogger("xhtml2pdf").setLevel(logging.ERROR)

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    out_pdf.unlink(missing_ok=True)
    try:
        with out_pdf.open("wb") as handle:
            status = pisa.CreatePDF(
                document,
                dest=handle,
                encoding="utf-8",
                link_callback=link_callback,
                **_resource_policy(),
            )
    except Exception as exc:
        out_pdf.unlink(missing_ok=True)
        raise GftdError(f"could not render the PDF: {exc}") from exc

    if status.err:
        out_pdf.unlink(missing_ok=True)
        raise GftdError(f"the PDF renderer reported {status.err} error(s)")

    missing = [name for name in REQUIRED_FONTS if name not in embedded_fonts(out_pdf)]
    if missing:
        out_pdf.unlink(missing_ok=True)
        raise GftdError(
            f"the PDF did not embed {', '.join(missing)}; Vietnamese text would show as boxes",
            hint=f"the fonts in {FONT_DIR} could not be read by the renderer",
        )

    return count_pages(out_pdf)


def _resource_policy() -> dict:
    """Let the renderer read our fonts and nothing else.

    xhtml2pdf 0.2.18 and later confine local reads to the working directory by
    default. Our fonts live in the installed package, outside wherever the user
    runs the command, so under that default every font was refused and the
    brief silently fell back to Helvetica. The document needs no other file and
    nothing from the network, so the policy allows exactly the font directory.
    Older versions have no policy, and read the paths `link_callback` returns.
    """
    try:
        from xhtml2pdf.config.resources import ResourceAccessPolicy
    except ImportError:  # pragma: no cover - xhtml2pdf before 0.2.18
        return {}
    return {"resource_policy": ResourceAccessPolicy(allow_remote=False, base_dir=FONT_DIR)}


def embedded_fonts(pdf: Path) -> set[str]:
    """The font names the PDF declares, without their subset prefix."""
    return {match.decode("ascii") for match in _BASE_FONT.findall(pdf.read_bytes())}


def count_pages(pdf: Path) -> int | None:
    """Page count from the raw PDF, or None if it cannot be determined.

    Two independent signals: `/Type /Page` objects, and `/Count` read *only*
    from a `/Type /Pages` node. They normally agree; taking the larger means a
    compressed page tree can never under-report and let an over-long brief slip
    past the budget.

    The `/Type /Pages` restriction matters. `/Count` also appears in the
    outline tree, where it counts bookmarks — the renderer emits one bookmark
    per heading, so a one-page brief with two headings reported two pages and
    could be rejected for a budget it was comfortably inside.

    Reading the bytes rather than asking the renderer keeps this usable for a
    PDF this tool did not produce — which is exactly what `verify` does.
    """
    try:
        raw = pdf.read_bytes()
    except OSError:
        return None
    by_object = len(_PAGE_OBJECT.findall(raw))
    tree_counts = [
        int(match.group(1))
        for body in (m.group(1) for m in _OBJECT.finditer(raw))
        if _PAGES_NODE.search(body)
        for match in [_COUNT.search(body)]
        if match
    ]
    best = max(by_object, max(tree_counts) if tree_counts else 0)
    return best or None


__all__ = ["FONT_DIR", "count_pages", "link_callback", "render_html"]
