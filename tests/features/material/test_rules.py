"""One case per rule, against the HTML generation.

A documented rule that never fires teaches the model a constraint nothing holds
it to — and `references/material/structure.md` is generated from the same table,
so the prose would promise it too. Each case makes one edit to the clean module.
"""

from __future__ import annotations

import re
from pathlib import Path

from get_fsa_training_done.features.material.core import rules

DECK = "01_Relational_Modelling.deck.html"
NOTE = "01_Relational_Modelling.html"
SECOND = "02_Querying.html"
LAB = "dbf_lab_01.html"


def test_the_shipped_module_is_clean(fired, module):
    """Everything else here is a deviation from this baseline."""
    assert fired(module) == set()


def cut(root: Path, name: str, pattern: str) -> None:
    """Remove the first match of a regex from a file."""
    path = root / name
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, "", text, count=1, flags=re.DOTALL)
    assert count == 1, f"{name} has no match for {pattern!r}"
    path.write_text(updated, encoding="utf-8")


# --- Naming and folders ---------------------------------------------------


def test_d01_a_filename_outside_the_convention_is_caught(fired, module):
    (module / NOTE).rename(module / "relational-modelling.html")
    assert "MAT-D01" in fired(module)


def test_d02_two_notes_claiming_one_index_are_caught(fired, module):
    (module / SECOND).rename(module / "01_Querying.html")
    assert "MAT-D02" in fired(module)


def test_d02_a_deck_and_its_note_share_an_index(fired, module):
    assert "MAT-D02" not in fired(module)


def test_d03_a_gap_in_the_indexes_warns(fired, module):
    (module / SECOND).rename(module / "04_Querying.html")
    assert "MAT-D03" in fired(module)


# --- Every document -------------------------------------------------------


def test_d21_a_missing_kind_is_caught(fired, module, edit):
    edit(module, NOTE, '<meta name="fsa:kind" content="note">\n', "")
    assert "MAT-D21" in fired(module / NOTE)


def test_d21_a_kind_that_disagrees_with_the_filename_is_caught(fired, module, edit):
    edit(module, NOTE, 'content="note"', 'content="lab"')
    assert "MAT-D21" in fired(module / NOTE)


def test_d22_inline_style_is_caught(fired, module, edit):
    edit(module, NOTE, "<h1>Relational Modelling</h1>", '<h1 style="color:red">Relational</h1>')
    assert "MAT-D22" in fired(module / NOTE)


def test_d22_a_style_element_is_caught(fired, module, edit):
    edit(module, NOTE, "</head>", "<style>h2 { color: red; }</style>\n</head>")
    assert "MAT-D22" in fired(module / NOTE)


def test_d22_a_deck_without_the_viewer_is_caught(fired, module, edit):
    edit(module, DECK, '<script src="_theme/deck.js" defer></script>\n', "")
    assert "MAT-D22" in fired(module / DECK)


def test_d23_an_unclosed_element_is_caught(fired, module, edit):
    edit(
        module,
        NOTE,
        '</ul>\n</section>\n\n<section data-part="why"',
        '</ul>\n\n<section data-part="why"',
    )
    assert "MAT-D23" in fired(module / NOTE)


def test_d10_a_code_block_without_a_language_is_caught(fired, module, edit):
    edit(module, NOTE, '<code class="language-sql">', "<code>")
    assert "MAT-D10" in fired(module / NOTE)


def test_d11_an_unknown_language_warns(fired, module, edit):
    edit(module, NOTE, "language-sql", "language-asciidoc")
    assert "MAT-D11" in fired(module / NOTE)


def test_d12_a_link_to_a_missing_file_is_caught(fired, module, edit):
    edit(module, NOTE, 'href="00_Study_Guide_Handbook.html"', 'href="00_Missing.html"')
    assert "MAT-D12" in fired(module / NOTE)


def test_d13_an_id_that_no_longer_exists_is_caught(fired, module, edit):
    edit(module, NOTE, 'id="worked-example"', 'id="example"')
    assert "MAT-D13" in fired(module)


def test_d24_an_image_without_alt_text_warns(fired, module, edit):
    (module / "shot.png").write_bytes(b"")
    edit(module, NOTE, "<h2>Keys</h2>", '<h2>Keys</h2>\n  <img src="shot.png">')
    assert "MAT-D24" in fired(module / NOTE)


def test_d16_vietnamese_outside_a_translation_warns(fired, module, edit):
    edit(module, NOTE, "An <strong>entity</strong> is", "Một <strong>thực thể</strong> là")
    assert "MAT-D16" in fired(module / NOTE)


def test_d16_a_translation_may_be_vietnamese(fired, module):
    translated = module / "01_Relational_Modelling_vn.html"
    translated.write_text(
        (module / NOTE)
        .read_text(encoding="utf-8")
        .replace('<html lang="en">', '<html lang="vi">')
        .replace("An <strong>entity</strong> is", "Một <strong>thực thể</strong> là"),
        encoding="utf-8",
    )
    assert "MAT-D16" not in fired(translated)
    assert "MAT-D02" not in fired(module)


def test_d16_a_translation_that_does_not_declare_vietnamese_warns(fired, module):
    translated = module / "01_Relational_Modelling_vn.html"
    translated.write_text((module / NOTE).read_text(encoding="utf-8"), encoding="utf-8")
    assert "MAT-D16" in fired(translated)


def test_d16_a_document_written_in_vietnamese_declares_it(fired, module, edit):
    """A module written in Vietnamese is not a translation: `lang="vi"` is enough."""
    edit(module, NOTE, '<html lang="en">', '<html lang="vi">')
    edit(module, NOTE, "An <strong>entity</strong> is", "Một <strong>thực thể</strong> là")
    edit(module, NOTE, "After this unit, learners can:", "Sau bài học này, học viên có thể:")
    rules_fired = fired(module / NOTE)
    assert "MAT-D16" not in rules_fired and "MAT-D06" not in rules_fired


def test_d19_an_er_relationship_without_cardinality_words_warns(fired, module, edit):
    edit(module, NOTE, '"1-n writes"', "writes")
    assert "MAT-D19" in fired(module / NOTE)


def test_d20_a_colour_fixed_in_a_diagram_warns(fired, module, edit):
    edit(module, NOTE, "erDiagram\n", "erDiagram\n    style AUTHOR fill:#f9f\n")
    assert "MAT-D20" in fired(module / NOTE)


# --- Lecture notes --------------------------------------------------------


def test_d06_the_wrong_opening_sentence_is_caught(fired, module, edit):
    edit(module, NOTE, "After this unit, learners can:", "This unit covers:")
    assert "MAT-D06" in fired(module / NOTE)


def test_d31_an_objective_without_its_code_is_caught(fired, module, edit):
    edit(module, NOTE, '<li data-objective="DBF-K1">Find the entities', "<li>Find the entities")
    assert "MAT-D31" in fired(module / NOTE)


def test_d29_a_missing_part_is_caught(fired, module, edit):
    edit(module, NOTE, 'data-part="why"', 'data-part="concept"')
    assert "MAT-D29" in fired(module / NOTE)


def test_d29_a_part_twice_is_caught(fired, module, edit):
    edit(module, NOTE, 'data-part="worked-example"', 'data-part="summary"')
    assert "MAT-D29" in fired(module / NOTE)


def test_d08_a_note_with_nowhere_to_go_next_is_caught(fired, module, edit):
    edit(module, NOTE, 'data-part="further-reading"', 'data-part="links"')
    assert "MAT-D08" in fired(module / NOTE)


def test_d09_a_thin_knowledge_check_warns(fired, module):
    path = module / SECOND
    text = path.read_text(encoding="utf-8")
    head, _, rest = text.partition('<section data-part="knowledge-check"')
    section, _, tail = rest.partition("</section>")
    first = section.split("</li>", 1)[0] + "</li>\n  </ol>\n"
    path.write_text(head + '<section data-part="knowledge-check"' + first + "</section>" + tail)
    assert "MAT-D09" in fired(path)


def test_d25_a_question_without_its_answer_is_caught(fired, module, edit):
    edit(
        module,
        NOTE,
        "<details><summary>Answer</summary><p>It identifies every row uniquely, and no smaller "
        "set of its columns does.</p></details>",
        "",
    )
    assert "MAT-D25" in fired(module / NOTE)


def test_d26_an_objective_no_question_tests_warns(fired, module, edit):
    edit(
        module,
        NOTE,
        '<li data-objective="DBF-K1">Choose a primary',
        '<li data-objective="DBF-K2">Choose a primary',
    )
    assert "MAT-D26" in fired(module / NOTE)


def test_d27_code_before_its_explanation_warns(fired, module, edit):
    edit(
        module,
        SECOND,
        "<h2>Grouping and Aggregation</h2>",
        "<h2>Grouping and Aggregation</h2>\n"
        '  <pre><code class="language-sql">SELECT 1;</code></pre>',
    )
    assert "MAT-D27" in fired(module / SECOND)


def test_d28_a_concept_with_nothing_to_try_warns(fired, module, edit):
    edit(module, SECOND, 'class="try-it"', 'class="exercise"')
    assert "MAT-D28" in fired(module / SECOND)


# --- Labs -----------------------------------------------------------------


def test_d17_a_lab_without_ordered_steps_is_caught(fired, module):
    path = module / LAB
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("<ol>", "<div>").replace("</ol>", "</div>"), encoding="utf-8")
    assert "MAT-D17" in fired(path)


def test_d17_a_lab_without_a_checklist_is_caught(fired, module, edit):
    edit(module, LAB, '<ul class="checklist">', "<ul>")
    assert "MAT-D17" in fired(module / LAB)


def test_d18_a_lab_with_no_duration_warns(fired, module, edit):
    edit(
        module,
        LAB,
        '<meta name="fsa:minutes" content="90">',
        '<meta name="fsa:minutes" content="long">',
    )
    assert "MAT-D18" in fired(module / LAB)


def test_d30_a_step_with_nothing_to_expect_warns(fired, module, edit):
    edit(module, LAB, 'class="expected"', 'class="result"')
    assert "MAT-D30" in fired(module / LAB)


# --- Slide decks ----------------------------------------------------------


def test_s01_a_deck_without_its_summary_is_caught(fired, module):
    cut(module, DECK, r'<section class="slide" data-layout="summary">.*?</section>\s*')
    assert "MAT-S01" in fired(module / DECK)


def test_s01_content_before_the_first_section_cover_is_caught(fired, module):
    path = module / DECK
    text = path.read_text(encoding="utf-8")
    first_section = text.index('<section class="slide" data-layout="section">')
    extra = (
        '<section class="slide" data-layout="content">\n  <h2 data-slot="title">Stray</h2>\n'
        "</section>\n\n"
    )
    path.write_text(text[:first_section] + extra + text[first_section:], encoding="utf-8")
    assert "MAT-S01" in fired(path)


def test_s02_an_unknown_layout_is_caught(fired, module, edit):
    edit(module, DECK, 'data-layout="closing"', 'data-layout="finale"')
    assert "MAT-S02" in fired(module / DECK)


def test_s02_a_slot_the_layout_lacks_is_caught(fired, module, edit):
    edit(module, DECK, 'data-slot="subtitle"', 'data-slot="tagline"')
    assert "MAT-S02" in fired(module / DECK)


def test_s02_content_outside_any_slot_is_caught(fired, module, edit):
    edit(
        module,
        DECK,
        '<h2 data-slot="title">Keys</h2>',
        '<h2 data-slot="title">Keys</h2>\n  <p>loose</p>',
    )
    assert "MAT-S02" in fired(module / DECK)


def test_s03_an_empty_required_slot_is_caught(fired, module, edit):
    edit(module, DECK, '<h2 data-slot="title">Keys</h2>', '<h2 data-slot="title"></h2>')
    assert "MAT-S03" in fired(module / DECK)


def test_s04_an_objective_without_its_code_is_caught(fired, module, edit):
    edit(
        module, DECK, '<li data-objective="DBF-K1">Choose a primary key', "<li>Choose a primary key"
    )
    assert "MAT-S04" in fired(module / DECK)


def test_s05_a_summary_that_cites_another_objective_is_caught(fired, module, edit):
    edit(
        module,
        DECK,
        '<li data-objective="DBF-K1">Entities are',
        '<li data-objective="DBF-K9">Entities are',
    )
    assert "MAT-S05" in fired(module / DECK)


def test_s06_a_slide_without_speaker_notes_warns(fired, module):
    cut(module, DECK, r'<aside class="notes">Put the catalogue.*?</aside>')
    assert "MAT-S06" in fired(module / DECK)


def test_s07_a_section_without_a_check_slide_warns(fired, module, edit):
    edit(
        module,
        DECK,
        'data-role="check">\n  <h2 data-slot="title">Is an email',
        '>\n  <h2 data-slot="title">Is an email',
    )
    assert "MAT-S07" in fired(module / DECK)


def test_s08_a_title_too_long_for_its_slot_warns(fired, module, edit):
    edit(
        module,
        DECK,
        "Prefer a surrogate key</h2>",
        "Why you should nearly always prefer a surrogate key here</h2>",
    )
    assert "MAT-S08" in fired(module / DECK)


def test_s08_a_line_of_code_too_wide_for_its_column_warns(fired, module, edit):
    edit(
        module,
        DECK,
        "  PRIMARY KEY (book_id,\n               author_id)",
        "  PRIMARY KEY (book_id, author_id), -- one long line",
    )
    assert "MAT-S08" in fired(module / DECK)


def test_s10_a_title_shrunk_far_below_the_template_warns(fired, module, edit, verify):
    edit(
        module,
        DECK,
        "Prefer a surrogate key</h2>",
        "Always prefer a surrogate key here</h2>",
    )
    assert "MAT-S10" in fired(module / DECK)
    relaxed = {f["rule"] for f in verify(module / DECK, "--min-fit", "0.5")["findings"]}
    assert "MAT-S10" not in relaxed


def test_s09_too_few_slides_for_the_minutes_warns(fired, module, edit):
    edit(
        module,
        DECK,
        '<meta name="fsa:minutes" content="60">',
        '<meta name="fsa:minutes" content="600">',
    )
    assert "MAT-S09" in fired(module / DECK)


def test_s09_the_range_is_a_flag(module, edit, verify):
    edit(
        module,
        DECK,
        '<meta name="fsa:minutes" content="60">',
        '<meta name="fsa:minutes" content="600">',
    )
    rules_fired = {
        f["rule"] for f in verify(module / DECK, "--minutes-per-slide", "1-40")["findings"]
    }
    assert "MAT-S09" not in rules_fired


# --- Exporting --------------------------------------------------------------


def test_x01_a_diagram_without_an_image_warns_only_for_export(fired, module, edit, verify):
    edit(module, NOTE, '<img src="img/catalogue_er.png"', '<span data-was="img"')
    assert "MAT-X01" not in fired(module / NOTE)
    assert "MAT-X01" in {f["rule"] for f in verify(module / NOTE, "--export")["findings"]}


def test_x01_a_diagram_with_its_image_passes(module, verify):
    assert "MAT-X01" not in {f["rule"] for f in verify(module / NOTE, "--export")["findings"]}


# X02 is found while drawing a deck's PDF; see test_export.py.


# --- Against the session plan --------------------------------------------


def test_c01_a_material_the_plan_names_but_which_is_missing(coverage_fired, module, plan_path):
    (module / DECK).unlink()
    assert "MAT-C01" in coverage_fired(plan_path, module)


def test_c02_a_worksheet_beside_a_used_lab_is_in_use(coverage_fired, module, plan_path):
    (module / "dbf_lab_01_worksheet.html").write_text("<h1>Worksheet</h1>", encoding="utf-8")
    assert coverage_fired(plan_path, module) == set()


def test_c02_a_worksheet_with_no_lab_warns(coverage_fired, module, plan_path):
    (module / "dbf_lab_07_worksheet.html").write_text("<h1>Worksheet</h1>", encoding="utf-8")
    assert "MAT-C02" in coverage_fired(plan_path, module)


def test_c02_a_material_no_session_uses_warns(coverage_fired, module, plan_path):
    (module / "03_Extra.html").write_text("<h1>Extra</h1>", encoding="utf-8")
    assert "MAT-C02" in coverage_fired(plan_path, module)


def test_c03_a_material_that_ignores_its_sessions_objectives_warns(
    coverage_fired, module, plan_path
):
    path = module / LAB
    path.write_text(path.read_text(encoding="utf-8").replace("DBF-K2", "DBF-K1"), "utf-8")
    assert "MAT-C03" in coverage_fired(plan_path, module)


def test_c04_an_objective_the_syllabus_does_not_define_warns(
    coverage_fired, module, plan_path, syllabus_path
):
    text = plan_path.read_text(encoding="utf-8").replace("DBF-K2", "DBF-K9")
    plan_path.write_text(text, encoding="utf-8")
    assert "MAT-C04" in coverage_fired(plan_path, module, "--syllabus", str(syllabus_path))


def test_a_markdown_file_is_not_teaching_material(coverage_fired, module, plan_path):
    """Material is HTML; a `.md` the plan names for a lecture is a gap."""
    text = plan_path.read_text(encoding="utf-8").replace("02_Querying.html", "02_Querying.md")
    plan_path.write_text(text, encoding="utf-8")
    (module / SECOND).rename(module / "02_Querying.md")
    assert "MAT-C01" in coverage_fired(plan_path, module)


def test_another_skills_files_are_never_reported_missing(module, plan_path, capsys):
    """The plan also names a quiz and an exam. They belong to the assessment
    feature, and reporting them here would send someone to write the wrong thing."""
    import json

    from get_fsa_training_done.cli import main

    capsys.readouterr()
    main(["material", "coverage", "--schedule", str(plan_path), "--dir", str(module), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["facts"]["owned by another feature"] == 2
    assert payload["findings"] == []


# --- Coverage of the rulebook --------------------------------------------


def test_every_rule_has_a_case():
    here = Path(__file__).parent
    source = "".join(path.read_text(encoding="utf-8") for path in here.glob("test_*.py"))
    assert [rule.id for rule in rules.RULES if rule.id not in source] == []


def test_no_duplicate_rule_ids():
    ids = [rule.id for rule in rules.RULES]
    assert len(ids) == len(set(ids))


# --- Review fixes: parsing, links, images ------------------------------------


def test_omitted_end_tags_still_count_every_step(fired, module):
    """HTML lets `</li>` and `</p>` go unwritten; the steps are still three."""
    from get_fsa_training_done.features.material.core import dom
    from get_fsa_training_done.features.material.core.checks import top_items

    document = dom.parse_text(
        "<html><body><ol><li><p>A<p class=expected>a<li><p>B<p class=expected>b"
        "<li>C</ol></body></html>"
    )
    assert [item.text() for item in top_items(document.body)] == ["Aa", "Bb", "C"]
    assert document.problems == []


def test_an_unclosed_paragraph_does_not_swallow_the_notes(module):
    from get_fsa_training_done.features.material.core import deck, dom

    document = dom.parse_text(
        '<html><body class="fsa-deck"><section class="slide" data-layout="content">'
        '<div data-slot="body"><p>text</div><aside class="notes">said</aside></section>'
        "</body></html>"
    )
    slide = deck.read(document)[0]
    assert slide.notes is not None and slide.notes.text() == "said"


def test_links_with_a_query_a_scheme_or_an_escape_resolve(fired, module, edit):
    (module / "a b.html").write_text("<p>x</p>", encoding="utf-8")
    edit(
        module,
        NOTE,
        "<h2>Keys</h2>",
        '<h2>Keys</h2>\n  <p><a href="02_Querying.html?print=1">q</a> <a href="tel:+84123">t</a> '
        '<a href="a%20b.html">s</a> <a href="javascript:void(0)">j</a></p>',
    )
    assert "MAT-D12" not in fired(module / NOTE)


def test_s08_measures_a_break_as_a_new_line(fired, module, edit):
    """`<br>` is a line in the browser and the .pptx, so verify counts it too."""
    edit(
        module,
        DECK,
        '<h2 data-slot="title">Prefer a surrogate key</h2>',
        '<h2 data-slot="title">Prefer<br>a<br>surrogate<br>key</h2>',
    )
    assert "MAT-S08" in fired(module / DECK)


def test_a_picture_slot_may_be_the_image_itself(fired, module, edit):
    (module / "pic.png").write_bytes((module / "img" / "catalogue_er.png").read_bytes())
    edit(
        module,
        DECK,
        '<section class="slide" data-layout="closing"></section>',
        '<section class="slide" data-layout="content-picture">\n'
        '  <h2 data-slot="title">A picture</h2>\n'
        '  <div data-slot="body"><p>Beside it.</p></div>\n'
        '  <img data-slot="picture" src="pic.png" alt="The catalogue">\n'
        '  <aside class="notes">Point at the picture and name each table in it, one by one,'
        " before moving on to the summary.</aside>\n</section>\n\n"
        '<section class="slide" data-layout="closing"></section>',
    )
    rules_fired = fired(module / DECK)
    assert "MAT-S03" not in rules_fired and "MAT-S02" not in rules_fired


def test_x03_an_svg_or_an_outside_image_warns_for_export(module, edit, verify):
    (module / "img" / "d.svg").write_text("<svg/>", encoding="utf-8")
    (module.parent / "outside.png").write_bytes((module / "img" / "catalogue_er.png").read_bytes())
    edit(
        module,
        NOTE,
        "<h2>Keys</h2>",
        '<h2>Keys</h2>\n  <img src="img/d.svg" alt="d">\n  <img src="../outside.png" alt="o">',
    )
    found = [f for f in verify(module / NOTE, "--export")["findings"] if f["rule"] == "MAT-X03"]
    assert len(found) == 2
    assert "MAT-X03" not in {f["rule"] for f in verify(module / NOTE)["findings"]}
