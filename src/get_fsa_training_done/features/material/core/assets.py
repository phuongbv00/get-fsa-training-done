"""What a link or an image `src` in a document points at.

One reading for `verify` and both exporters, so they agree on which references
are local files, which file each names, and which an export may embed: a link
with any scheme (`https:`, `mailto:`, `tel:`…) is not a file; a query or a
fragment is not part of the file name; `%20` is a space.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlsplit

#: What PowerPoint and the PDF writer can place. An SVG has to be exported to
#: PNG first.
RASTER = (".png", ".jpg", ".jpeg", ".gif")


def is_external(href: str) -> bool:
    """A reference to something other than a file beside the document."""
    parts = urlsplit(href.strip())
    return bool(parts.scheme or parts.netloc)


def split(href: str) -> tuple[str, str]:
    """The file part, decoded, and the fragment of a local reference."""
    parts = urlsplit(href.strip())
    return unquote(parts.path), unquote(parts.fragment)


def resolve(document: Path, href: str) -> Path | None:
    """The local file `href` names, relative to `document`; None if it names none."""
    if not href or is_external(href):
        return None
    target, _ = split(href)
    if not target:
        return None
    return (document.parent / target).resolve()


def inside(document: Path, path: Path) -> bool:
    """Is `path` within the document's own folder?"""
    try:
        path.resolve().relative_to(document.parent.resolve())
    except ValueError:
        return False
    return True


def embeddable(document: Path, src: str) -> tuple[Path | None, str]:
    """The image file an export may embed for `src`, or why it may not.

    An export embeds only images inside the module's folder: a `src` reaching
    out with `../../` would put an unrelated file into a deck handed to a class.
    """
    if is_external(src):
        return None, f"{src} is not a local file"
    path = resolve(document, src)
    if path is None:
        return None, "no src"
    if not inside(document, path):
        return None, f"{src} is outside the module's folder"
    if not path.is_file():
        return None, f"{src} does not exist"
    if path.suffix.lower() not in RASTER:
        return None, f"{path.name} is not PNG, JPEG or GIF"
    return path, ""


__all__ = ["RASTER", "embeddable", "inside", "is_external", "resolve", "split"]
