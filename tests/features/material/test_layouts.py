"""The layout table against the template it was read from.

`core/layouts.py` is the single source for the deck's HTML, its stylesheet, the
rules and the exporter. These check it still agrees with the shipped
`fsa_base.pptx` — a slot pointing at a placeholder the template does not have
would export to nowhere, silently.
"""

from __future__ import annotations

import pytest

from get_fsa_training_done.features.material.core import export_pptx, layouts

THEME = export_pptx.BASE.parent


@pytest.fixture(scope="module")
def template():
    pptx = pytest.importorskip("pptx")
    return pptx.Presentation(str(export_pptx.BASE))


def test_the_base_carries_no_slides(template):
    assert len(template.slides) == 0


def test_every_layout_exists_in_the_template(template):
    names = {layout.name for layout in template.slide_layouts}
    assert [layout.pptx_name for layout in layouts.LAYOUTS if layout.pptx_name not in names] == []


def test_every_slot_names_a_placeholder_its_layout_has(template):
    by_name = {layout.name: layout for layout in template.slide_layouts}
    missing = []
    for layout in layouts.LAYOUTS:
        indexes = {shape.placeholder_format.idx for shape in by_name[layout.pptx_name].placeholders}
        missing += [
            f"{layout.name}.{slot.name}"
            for slot in layout.slots
            if slot.idx is not None and slot.idx not in indexes
        ]
    assert missing == []


def test_the_toc_rows_are_placeholders_of_the_toc_layout(template):
    toc = next(layout for layout in template.slide_layouts if layout.name == "Table of Contents")
    by_idx = {shape.placeholder_format.idx: shape for shape in toc.placeholders}
    width, height = template.slide_width, template.slide_height
    for row in layouts.TOC_ROWS:
        for idx, box in row:
            shape = by_idx[idx]
            assert abs(shape.left * 100 / width - box.left) < 0.1, idx
            assert abs(shape.top * 100 / height - box.top) < 0.1, idx


# --- Fidelity: every slot styled as the template styles its placeholder ---------

FONT_NAMES = {"+mn-lt": layouts.MINOR}
ALIGN = {"l": "left", "ctr": "center"}
ANCHOR = {"t": "top", "ctr": "middle", "b": "bottom"}


def _deviation(layout: str, slot: str, field: str) -> bool:
    for (want_layout, want_slot, want_field), _reason in layouts.DEVIATIONS.items():
        if want_field != field:
            continue
        if want_layout not in ("*", layout):
            continue
        if want_slot == slot or (want_slot.endswith("*") and slot.startswith(want_slot[:-1])):
            return True
    return False


def test_every_slot_is_styled_as_its_placeholder(template):
    """Size, weight, slant, face, colour, alignment and anchor, as PowerPoint
    resolves them through the layout, the master and the theme."""
    from .template_style import resolve

    by_name = {layout.name: layout for layout in template.slide_layouts}
    differences = []
    for layout in layouts.LAYOUTS:
        for slot in layout.slots:
            if slot.idx is None or slot.kind == layouts.PICTURE:
                continue
            style = resolve(template, by_name[layout.pptx_name], slot.idx)
            expected = {
                "size": style.size,
                "bold": style.bold,
                "italic": style.italic,
                "font": FONT_NAMES.get(style.font, style.font),
                "colour": style.colour,
                "align": ALIGN.get(style.align, style.align),
                "anchor": ANCHOR.get(style.anchor, style.anchor),
            }
            for field, want in expected.items():
                have = getattr(slot, field)
                if have != want and not _deviation(layout.name, slot.name, field):
                    differences.append(f"{layout.name}.{slot.name}.{field}: {have!r} != {want!r}")
    assert differences == []


def test_every_slot_sits_where_its_placeholder_does(template):
    by_name = {layout.name: layout for layout in template.slide_layouts}
    width, height = template.slide_width, template.slide_height
    differences = []
    for layout in layouts.LAYOUTS:
        shapes = {sh.placeholder_format.idx: sh for sh in by_name[layout.pptx_name].placeholders}
        for slot in layout.slots:
            if slot.idx is None:
                continue
            shape = shapes[slot.idx]
            actual = {
                "left": shape.left * 100 / width,
                "top": shape.top * 100 / height,
                "width": shape.width * 100 / width,
                "height": shape.height * 100 / height,
            }
            for field, want in actual.items():
                if abs(getattr(slot.box, field) - want) > 0.15 and not _deviation(
                    layout.name, slot.name, field
                ):
                    differences.append(f"{layout.name}.{slot.name}.{field}")
    assert differences == []


def test_the_closing_slide_is_the_one_the_template_samples():
    """The template's own sample ends on the photograph of its Diversity layout."""
    assert layouts.BY_NAME["closing"].pptx_name == "Diversity"


# --- Fitting text ---------------------------------------------------------------


def test_a_short_title_keeps_the_templates_size():
    title = layouts.BY_NAME["content"].slot("title")
    assert layouts.fit_scale(title, "Keys") == 1.0


def test_a_long_title_shrinks_in_steps_to_one_line():
    title = layouts.BY_NAME["content"].slot("title")
    scale = layouts.fit_scale(title, "Which normal form does this break?")
    assert scale < 1.0 and scale in layouts.FIT_SCALES
    size = title.size * scale
    width = title.box.width_pt - 2 * layouts.INSET_X
    assert layouts.lines_needed("Which normal form does this break?", width, size, True) == 1


def test_a_title_too_long_to_fit_is_reported_not_shrunk_further():
    title = layouts.BY_NAME["content"].slot("title")
    text = "A title so long that no reasonable shrinking could ever fit it in the band"
    assert layouts.fit_scale(title, text) == layouts.FIT_SCALES[-1]
    assert layouts.overflows(title, text)


def test_the_stylesheet_carries_the_fit_constants():
    """deck.js reads them from layouts.css; the exporters from layouts.py."""
    css = (THEME / "layouts.css").read_text(encoding="utf-8")
    assert "--fit-scales: " + " ".join(f"{s:g}" for s in layouts.FIT_SCALES) in css
    assert f"--fit-char-em-bold: {layouts.CHAR_EM[True]:g}" in css


def test_the_template_embeds_no_fonts():
    """Calibri and Segoe UI are Microsoft's to license, not ours to ship."""
    import zipfile

    with zipfile.ZipFile(export_pptx.BASE) as package:
        assert not [name for name in package.namelist() if name.startswith("ppt/fonts/")]


def test_every_background_ships():
    for background in layouts.BACKGROUNDS:
        assert (THEME / "img" / f"{background}.jpg").is_file(), background
    assert (THEME / "img" / "band.jpg").is_file()


def test_slots_stay_on_the_slide():
    for layout in layouts.LAYOUTS:
        for slot in layout.slots:
            box = slot.box
            assert box.left + box.width <= 100.5, f"{layout.name}.{slot.name}"
            assert box.top + box.height <= 100.5, f"{layout.name}.{slot.name}"


def test_slot_names_are_unique_within_a_layout():
    for layout in layouts.LAYOUTS:
        names = [slot.name for slot in layout.slots]
        assert len(names) == len(set(names)), layout.name


def test_the_theme_stays_small():
    """It is copied into every module folder and shipped in every install."""
    total = sum(path.stat().st_size for path in THEME.rglob("*") if path.is_file())
    assert total < 2 * 1024 * 1024


FIT_SAMPLES = (
    "Keys",
    "Prefer a surrogate key",
    "Which normal form does this break?",
    "Entities and relationships",
    "Lesson 1 · Relational Modelling",
    "03.\nNormalization",
    "Keys\nand joins",
    "A title so long that no reasonable shrinking could ever fit it in the band",
    "Thank you!",
)


def test_the_viewers_fit_is_the_pythons(tmp_path):
    """deck.js picks the same step as layouts.fit_scale, slot by slot.

    The browser, the .pptx and the .pdf only agree if the JavaScript port of the
    estimate stays a port; this runs it in Node on every fitting slot.
    """
    import json
    import shutil
    import subprocess

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is not installed")
    source = (THEME / "deck.js").read_text(encoding="utf-8")
    port = source.split("/* fit:begin", 1)[1].split("/* fit:end */", 1)[0]
    port = "/*" + port

    cases = []
    for layout in layouts.LAYOUTS:
        for slot in layout.slots:
            if not slot.fits:
                continue
            for text in FIT_SAMPLES:
                cases.append(
                    {
                        "text": text,
                        "width": slot.box.width_pt - 2 * layouts.INSET_X,
                        "height": slot.box.height_pt - 2 * layouts.INSET_Y,
                        "size": slot.size,
                        "charEm": layouts.CHAR_EM[slot.bold],
                        "python": layouts.fit_scale(slot, text),
                        "where": f"{layout.name}.{slot.name}",
                    }
                )
    script = tmp_path / "fit.js"
    script.write_text(
        port
        + f"\nvar cases = {json.dumps(cases)};\n"
        + f"var scales = {json.dumps(list(layouts.FIT_SCALES))};\n"
        + "var bad = cases.filter(function (c) {\n"
        + "  return pickScale(c.text, c.width, c.height, c.size, c.charEm, "
        + f"{layouts.SPACE_EM}, {layouts.LINE_HEIGHT}, scales) !== c.python;\n"
        + "}).map(function (c) { return c.where + ': ' + JSON.stringify(c.text); });\n"
        + "console.log(JSON.stringify(bad));\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [node, str(script)], capture_output=True, text=True, encoding="utf-8", check=True
    )
    assert json.loads(result.stdout) == []
