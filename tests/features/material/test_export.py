"""Exporting, and the theme.

The HTML is the source; these check that what is derived from it says the same
thing — every slide in the template's own layout, every slot's text where its
placeholder is — and that the theme a module links to is the one the exporter
draws.
"""

from __future__ import annotations

import json

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.features.material.core import deck as deck_mod
from get_fsa_training_done.features.material.core import dom, layouts

DECK = "01_Relational_Modelling.deck.html"
NOTE = "dbf_lecture_note.html"


@pytest.fixture
def pptx():
    return pytest.importorskip("pptx")


def test_a_deck_exports_into_the_templates_own_layouts(module, pptx):
    assert main(["material", "export", "pptx", str(module / DECK)]) == 0
    out = module / "01_Relational_Modelling.deck.pptx"
    deck = pptx.Presentation(str(out))

    source = deck_mod.read(dom.parse(module / DECK))
    assert [slide.slide_layout.name for slide in deck.slides] == [
        slide.layout.pptx_name for slide in source
    ]


def test_an_exported_deck_carries_its_text_notes_and_answers(module, pptx):
    main(["material", "export", "pptx", str(module / DECK)])
    deck = pptx.Presentation(str(module / "01_Relational_Modelling.deck.pptx"))
    slides = list(deck.slides)

    def texts(slide):
        return [shape.text_frame.text for shape in slide.shapes if shape.has_text_frame]

    assert "Databases" in texts(slides[0])
    # The table of contents is derived from the section covers.
    assert {"Entities and relationships", "Keys", "Normalization"} <= set(texts(slides[1]))
    # Defaults the template only shows as a prompt are written out.
    assert "Lesson Objectives" in texts(slides[2])
    assert "Thank you!" in texts(slides[-1])
    # Section covers number themselves.
    assert any(text.startswith("02.") for text in texts(slides[7]))
    # Speaker notes travel; a check slide's answer goes to the notes, not the slide.
    check = slides[6]
    notes = check.notes_slide.notes_text_frame.text
    assert "Answer: Member" in notes
    assert not any("Member: it has facts" in text for text in texts(check))


def test_unused_placeholders_are_removed_not_left_as_prompts(module, pptx):
    main(["material", "export", "pptx", str(module / DECK)])
    deck = pptx.Presentation(str(module / "01_Relational_Modelling.deck.pptx"))
    toc = list(deck.slides)[1]
    # Three sections: the title and three section titles stay; rows four and
    # five are gone, and each number is drawn as a circle of its own.
    assert len(list(toc.placeholders)) == 1 + 3
    circles = [shape for shape in toc.shapes if not shape.is_placeholder]
    assert [shape.text_frame.text for shape in circles] == ["1", "2", "3"]


def test_a_long_title_exports_at_the_same_step_the_browser_picks(module, pptx):
    from get_fsa_training_done.features.material.core import layouts as L

    main(["material", "export", "pptx", str(module / DECK)])
    deck = pptx.Presentation(str(module / "01_Relational_Modelling.deck.pptx"))
    slide = list(deck.slides)[14]
    title = next(shape for shape in slide.placeholders if shape.placeholder_format.idx == 1)
    run = title.text_frame.paragraphs[0].runs[0]
    spec = L.BY_NAME["content"].slot("title")
    expected = spec.size * L.fit_scale(spec, "Which form does it break?")
    assert run.font.size.pt == pytest.approx(expected, abs=0.5)
    assert run.font.bold and run.font.name == spec.font


def test_only_a_deck_exports_to_pptx(module):
    from get_fsa_training_done.errors import UsageError

    with pytest.raises(UsageError, match="only a deck"):
        main(["material", "export", "pptx", str(module / NOTE)])


def test_export_refuses_a_document_with_errors(module, edit):
    edit(module, DECK, 'data-layout="closing"', 'data-layout="finale"')
    assert main(["material", "export", "pdf", str(module / DECK)]) == 1
    assert not (module / "01_Relational_Modelling.deck.pdf").exists()


def test_a_deck_exports_to_one_pdf_page_per_slide(module):
    pytest.importorskip("reportlab")
    from get_fsa_training_done.features.common.render import pdf as pdf_mod

    assert main(["material", "export", "pdf", str(module / DECK)]) == 0
    out = module / "01_Relational_Modelling.deck.pdf"
    assert pdf_mod.count_pages(out) == 17


def test_x02_a_slot_that_cannot_fit_is_reported(module, capsys):
    pytest.importorskip("reportlab")
    path = module / DECK
    items = "".join(
        f"<li>An item long enough to need its own line, number {n}</li>" for n in range(40)
    )
    text = path.read_text(encoding="utf-8").replace(
        "<li>Name entities in the singular</li>", items, 1
    )
    path.write_text(text, encoding="utf-8")
    capsys.readouterr()
    main(["material", "export", "pdf", str(path)])
    assert "MAT-X02" in capsys.readouterr().out


def test_an_svg_picture_reaches_the_pptx_and_the_pdf(module, pptx):
    """PowerPoint and the PDF writers place raster images: the SVG is drawn to a
    PNG for them rather than skipped."""
    pytest.importorskip("pypdfium2")
    assert main(["material", "export", "pptx", str(module / DECK)]) == 0
    slides = list(pptx.Presentation(str(module / "01_Relational_Modelling.deck.pptx")).slides)
    # Slide 5 is "Entities are nouns with facts", its picture an SVG.
    assert any(shape.shape_type == 13 for shape in slides[4].shapes)
    assert main(["material", "export", "pdf", str(module / DECK)]) == 0
    data = (module / "01_Relational_Modelling.deck.pdf").read_bytes()
    assert data.count(b"/Subtype /Image") >= 3  # the ER diagram and both drawings


def test_an_svg_is_drawn_in_the_modules_fonts():
    from get_fsa_training_done.features.material.core import svg

    text = svg.normalise_fonts(
        '<svg xmlns="http://www.w3.org/2000/svg"><text font-family="Arial">a</text>'
        '<text style="font-family: Consolas; fill: red">b</text></svg>'
    )
    assert 'font-family="FsaSans"' in text and "font-family: FsaMono" in text
    assert text.startswith('<svg font-family="FsaSans"')


def test_a_note_exports_to_an_a4_pdf(module):
    pytest.importorskip("xhtml2pdf")
    from get_fsa_training_done.features.common.render import pdf as pdf_mod

    assert main(["material", "export", "pdf", str(module / NOTE)]) == 0
    assert pdf_mod.count_pages(module / "dbf_lecture_note.pdf") >= 2


# --- The theme ----------------------------------------------------------------


def test_init_copies_the_theme_without_the_template(module):
    assert main(["material", "init", "--dir", str(module)]) == 0
    theme = module / "_theme"
    assert (theme / "fsa.css").is_file() and (theme / "deck.js").is_file()
    assert not (theme / "fsa_base.pptx").exists()
    for background in layouts.BACKGROUNDS:
        assert (theme / "img" / f"{background}.jpg").is_file()


def test_init_is_safe_to_run_again(module):
    main(["material", "init", "--dir", str(module)])
    (module / "_theme" / "stale.txt").write_text("old", encoding="utf-8")
    assert main(["material", "init", "--dir", str(module)]) == 0
    assert not (module / "_theme" / "stale.txt").exists()


def test_verify_reports_json(module, capsys):
    capsys.readouterr()
    main(["material", "verify", str(module), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["facts"]["deck"] == 1 and payload["facts"]["note"] == 1


# --- Review fixes: what the exports carry ------------------------------------


def test_text_beside_a_list_survives_and_a_paragraph_item_is_not_doubled():
    from get_fsa_training_done.features.material.core import rich

    body = dom.parse_text(
        '<div data-slot="body">Intro <strong>a lot</strong>:<ul><li><p>one</p><p>more</p></li>'
        "</ul>and after</div>"
    ).root.elements[0]
    assert [(b.kind, b.level, b.text()) for b in rich.blocks(body)] == [
        ("para", 0, "Intro a lot:"),
        ("bullet", 0, "one"),
        ("para", 1, "more"),
        ("para", 0, "and after"),
    ]


def test_inline_markup_keeps_a_title_on_one_line():
    from get_fsa_training_done.features.material.core import rich

    title = dom.parse_text('<h2 data-slot="title">Using <code>JOIN</code> well</h2>').root.elements[
        0
    ]
    blocks = rich.blocks(title)
    assert len(blocks) == 1 and blocks[0].text() == "Using JOIN well"


def test_a_slot_is_a_block_so_inline_markup_flows():
    """A flex slot stacked `Using`, `<code>JOIN</code>` and `well` as three lines."""
    css = (layouts_theme() / "fsa.css").read_text(encoding="utf-8")
    rule = css.split(".slide > [data-slot],", 1)[1].split("}", 1)[0]
    assert "display: block" in rule and "display: flex" not in rule


def layouts_theme():
    from get_fsa_training_done.features.material.core import export_pptx

    return export_pptx.BASE.parent


def test_a_note_pdf_carries_its_images_not_the_diagram_source(module):
    pytest.importorskip("xhtml2pdf")
    assert main(["material", "export", "pdf", str(module / NOTE)]) == 0
    data = (module / "dbf_lecture_note.pdf").read_bytes()
    assert b"/Subtype /Image" in data or b"/Subtype/Image" in data
    assert b"erDiagram" not in data


def test_a_note_pdf_draws_each_of_its_images(module, edit):
    """xhtml2pdf 0.2.23 printed every image after the first as a copy of it."""
    pytest.importorskip("xhtml2pdf")
    import hashlib
    import re

    from PIL import Image

    for name, colour in (("green.png", (80, 183, 72)), ("blue.png", (3, 78, 161))):
        Image.new("RGB", (300, 120), colour).save(module / "img" / name)
    edit(
        module,
        NOTE,
        "<h3>Keys</h3>",
        '<h3>Keys</h3>\n  <figure><img src="img/green.png" alt="green"><figcaption>One.'
        '</figcaption></figure>\n  <figure><img src="img/blue.png" alt="blue"></figure>',
    )
    assert main(["material", "export", "pdf", str(module / NOTE)]) == 0
    data = (module / "dbf_lecture_note.pdf").read_bytes()
    streams = re.findall(rb"/Subtype /Image.*?stream\r?\n(.*?)endstream", data, re.S)
    assert len({hashlib.sha256(s).hexdigest() for s in streams}) >= 3


def test_a_note_pdf_sets_a_caption_under_its_picture(module):
    """Without block rules a figure's caption ran on beside its image."""
    from get_fsa_training_done.features.material.core import export_pdf

    html = export_pdf._print_html(dom.parse(module / NOTE))
    for rule in ("figure { display: block", "figcaption { display: block", "td code, th code"):
        assert rule in html


def test_a_backslash_in_the_metadata_does_not_break_the_pdf(module, edit):
    pytest.importorskip("xhtml2pdf")
    edit(module, NOTE, 'content="SQL:2016 · PostgreSQL 16"', r'content="C:\dev\tools"')
    assert main(["material", "export", "pdf", str(module / NOTE)]) == 0


def test_an_image_outside_the_module_is_not_embedded(module, edit, capsys, pptx):
    (module.parent / "secret.png").write_bytes((module / "img" / "catalogue_er.png").read_bytes())
    edit(module, DECK, 'src="img/catalogue_er.png"', 'src="../secret.png"')
    capsys.readouterr()
    main(["material", "export", "pptx", "--force", str(module / DECK)])
    out = capsys.readouterr().out
    assert "outside the module's folder" in out
    deck = pptx.Presentation(str(module / "01_Relational_Modelling.deck.pptx"))
    pictures = [shape for shape in list(deck.slides)[5].shapes if shape.shape_type == 13]
    assert pictures == []


# --- The document's language -------------------------------------------------


def _vietnamese(module, name):
    path = module / name
    path.write_text(
        path.read_text(encoding="utf-8").replace('<html lang="en">', '<html lang="vi">'),
        encoding="utf-8",
    )


def test_a_vietnamese_deck_exports_its_defaults_in_vietnamese(module, pptx):
    _vietnamese(module, DECK)
    main(["material", "export", "pptx", str(module / DECK)])
    slides = list(pptx.Presentation(str(module / "01_Relational_Modelling.deck.pptx")).slides)

    def texts(slide):
        return [shape.text_frame.text for shape in slide.shapes if shape.has_text_frame]

    assert "Nội dung" in texts(slides[1])
    assert "Mục tiêu bài học" in texts(slides[2])
    assert "Cảm ơn!" in texts(slides[-1])
    assert any("✗ Sai" in text for text in texts(slides[9]))


def test_a_vietnamese_note_pdf_numbers_its_parts_and_speaks_vietnamese(module):
    pytest.importorskip("xhtml2pdf")
    from get_fsa_training_done.features.material.core import export_pdf

    _vietnamese(module, NOTE)
    html = export_pdf._print_html(dom.parse(module / NOTE))
    assert "Databases" in html and "1. Objectives" in html
    assert "✗ SAI" in html
    # Each objective's code follows its text, as the browser shows it.
    first_tag = html.index('class="code-tag"')
    assert html.index("Find the entities") < first_tag


def test_a_note_pdf_numbers_its_review_questions_and_tags_them_inline(module):
    """xhtml2pdf drops the number of an item that opens with a paragraph, and a
    tag beside that paragraph prints as a bar across the page."""
    from get_fsa_training_done.features.material.core import export_pdf

    html = export_pdf._print_html(dom.parse(module / NOTE))
    questions = html.split("Review Questions", 1)[1]
    assert "<p>1. What makes a column set a candidate key?" in questions
    assert "<p>10. How would you check" in questions
    assert 'candidate key? <span class="code-tag">' in questions


def test_a_note_pdf_jumps_to_its_topics(module):
    """xhtml2pdf jumps only to `<a name>`, never to an `id`: without one at each
    topic, the module map's and the syllabus map's links went nowhere."""
    pytest.importorskip("xhtml2pdf")
    import re

    from get_fsa_training_done.features.material.core import export_pdf

    html = export_pdf._print_html(dom.parse(module / NOTE))
    for anchor in ("relational-modelling", "querying", "environment"):
        assert f'<a name="{anchor}"></a>' in html
    assert main(["material", "export", "pdf", str(module / NOTE)]) == 0
    data = (module / "dbf_lecture_note.pdf").read_bytes()
    # Two module-map rows and two syllabus-map items jump inside the file.
    links, urls = len(re.findall(rb"/Subtype /Link", data)), len(re.findall(rb"/URI \(", data))
    assert links - urls >= 4


def test_a_note_pdf_names_the_pdf_a_sibling_link_points_at(module):
    """A PDF cannot open the HTML beside it: the link keeps its words and says
    which exported file to open."""
    from get_fsa_training_done.features.material.core import export_pdf

    html = export_pdf._print_html(dom.parse(module / NOTE))
    assert 'href="01_Relational_Modelling.deck.html"' not in html
    assert '<p class="xref-file">01_Relational_Modelling.deck.pdf</p>' in html  # in the map
    assert '<span class="xref-file">(01_Relational_Modelling.deck.pdf)</span>' in html  # in text
    lab = export_pdf._print_html(dom.parse(module / "dbf_lab_01.html"))
    assert "(dbf_lecture_note.pdf)" in lab


def test_a_note_pdf_numbers_a_list_of_plain_items_the_same_way(module):
    """How to Study's items open with text, not a paragraph: they are numbered by
    the same hand, so a list never mixes the renderer's numbers with written ones."""
    from get_fsa_training_done.features.material.core import export_pdf

    html = export_pdf._print_html(dom.parse(module / NOTE))
    routine = html.split("How to Study This Module", 1)[1].split("</ol>", 1)[0]
    assert routine.count('class="numbered"') == 3
    assert "3. " in routine and "4. " not in routine


def test_a_vietnamese_lab_pdf_names_its_session_in_vietnamese(module):
    """The note covers a module; a lab serves one session and says which."""
    pytest.importorskip("xhtml2pdf")
    from get_fsa_training_done.features.material.core import export_pdf

    _vietnamese(module, "dbf_lab_01.html")
    html = export_pdf._print_html(dom.parse(module / "dbf_lab_01.html"))
    assert "Buổi 1" in html and "90 phút" in html


def test_the_theme_labels_follow_the_page_language():
    from get_fsa_training_done.features.material.core import i18n

    css = (layouts_theme() / "layouts.css").read_text(encoding="utf-8")
    for lang in i18n.languages()[1:]:
        assert f".fsa-doc .try-it:lang({lang})::before" in css
        assert f":root:lang({lang})" in css
    assert 'content: "Try it"' not in (layouts_theme() / "fsa.css").read_text(encoding="utf-8")


def test_the_syllabus_map_is_headed_in_the_notes_language(module, syllabus_path):
    path = module / NOTE
    _vietnamese(module, NOTE)
    main(
        [
            "material",
            "derive",
            "syllabus-map",
            "--syllabus",
            str(syllabus_path),
            "--note",
            str(path),
            "--write",
        ]
    )
    assert "<h2>Bản đồ syllabus</h2>" in path.read_text(encoding="utf-8")
