"""The print-tuned HTML shell wrapped around a rendered brief.

Tuned for A4 print rather than screen: explicit page box and margins, point-based
type, `break-after: avoid` on headings so a section title never strands at the
foot of a page, and `break-inside: avoid` on table rows and code blocks.

Fonts are **embedded, not named**. Naming system faces worked while headless
Chrome did the rendering — it resolved whatever the machine happened to have —
but the renderer has no such fallback, and a Vietnamese letter with no glyph
comes out as a blank box rather than an error. `core/fonts/` explains the two
families and why the mono one is not DejaVu's.
"""

from __future__ import annotations

import html as _html

from .markdown import to_html_body

#: Resolved to real files by `pdf.py`'s link callback, so the CSS never carries
#: a filesystem path and nothing here depends on the platform's path syntax.
FONT_CSS = """
@font-face { font-family: "FsaSans"; src: url("DejaVuSans.ttf"); }
@font-face { font-family: "FsaSans"; src: url("DejaVuSans-Bold.ttf"); font-weight: bold; }
@font-face { font-family: "FsaMono"; src: url("RobotoMono-Regular.ttf"); }
@font-face { font-family: "FsaMono"; src: url("RobotoMono-Bold.ttf"); font-weight: bold; }
"""

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "FsaSans";
  font-size: 10.5pt; line-height: 1.5; color: #1a1a1a; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1 { font-size: 20pt; margin: 0 0 .4em; line-height: 1.2; }
h2 { font-size: 15pt; margin: 1.4em 0 .5em; padding-bottom: .2em;
     border-bottom: 1px solid #d0d0d0; }
h3 { font-size: 12.5pt; margin: 1.2em 0 .4em; }
h4 { font-size: 11pt; margin: 1em 0 .3em; color: #333; }
h2, h3, h4 { break-after: avoid; }
p { margin: .5em 0; }
ul, ol { margin: .5em 0; padding-left: 1.6em; }
li { margin: .2em 0; }
li > ul, li > ol { margin: .2em 0; }
a { color: #0b5cad; text-decoration: none; }
hr { border: 0; border-top: 1px solid #d8d8d8; margin: 1.2em 0; }
code {
  font-family: "FsaMono";
  font-size: 9pt; background: #f2f3f5; padding: .1em .35em; border-radius: 3px;
}
pre {
  background: #f6f7f9; border: 1px solid #e2e4e8; border-radius: 5px;
  padding: .7em .9em; overflow-x: auto; break-inside: avoid; margin: .7em 0;
}
pre code { background: none; padding: 0; font-size: 8.6pt; line-height: 1.45; }
blockquote {
  margin: .8em 0; padding: .1em 1em; border-left: 3px solid #c7ccd4;
  background: #fafbfc; color: #333;
}
blockquote p { margin: .35em 0; }
table {
  border-collapse: collapse; width: 100%; margin: .8em 0; font-size: 9.3pt;
  break-inside: auto;
}
th, td { border: 1px solid #cfd3da; padding: .38em .55em; vertical-align: top; }
th { background: #eef1f5; font-weight: 600; }
tr { break-inside: avoid; }
tbody tr:nth-child(even) { background: #fafbfc; }
"""


def build_document(markdown: str, title: str, *, lang: str = "en") -> str:
    """A complete, self-contained HTML document — no external requests."""
    return (
        '<!DOCTYPE html><html lang="' + _html.escape(lang, quote=True) + '">'
        '<head><meta charset="utf-8">'
        f"<title>{_html.escape(title)}</title><style>{FONT_CSS}{CSS}</style></head>"
        f"<body>{to_html_body(markdown)}</body></html>"
    )
