# Embedded fonts

`render` embeds these rather than naming system faces, because the briefs are
often Vietnamese and system coverage is not something we can assume. Headless
Chrome used to paper over this by resolving whatever the machine had installed;
a pure-Python renderer has no such fallback, and an unmapped glyph comes out as
a blank box or a NUL byte rather than an error.

| File | Used for | Licence |
|---|---|---|
| `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf` | body text, headings, tables | DejaVu Fonts Licence (Bitstream Vera derivative) — `LICENSE-DejaVu.txt` |
| `RobotoMono-Regular.ttf`, `RobotoMono-Bold.ttf` | `code` and `pre` | Apache 2.0 — `LICENSE-RobotoMono.txt` |

Both are redistributable and are shipped unmodified.

## Why Roboto Mono and not DejaVu Sans Mono

DejaVu Sans covers all 146 precomposed Vietnamese letters. DejaVu Sans **Mono**
covers only 100 — it is missing every double-diacritic letter (`ề`, `ố`, `ữ`,
`ắ`, …). Vietnamese inside a code span or fenced block would render as NUL with
no warning. Roboto Mono covers all 146 and is a third of the size.

`tests/features/assessment/test_render.py` asserts that coverage, so swapping
either face for one with a narrower repertoire fails rather than silently
degrading a `_vn` brief.

## No italic face

`core/markdown.py` emits `<strong>` but never `<em>`, so an oblique face would
be ~600KB of nothing. If emphasis is ever added to the Markdown dialect, add
`DejaVuSans-Oblique.ttf` and a matching `@font-face` rule at the same time.
