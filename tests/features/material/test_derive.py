"""Deriving the lecture note's syllabus map."""

from __future__ import annotations

from get_fsa_training_done.cli import main
from get_fsa_training_done.features.material.core import dom, syllabus_map

NOTE = "dbf_lecture_note.html"


def argv(module, syllabus, *extra):
    return [
        "material",
        "derive",
        "syllabus-map",
        "--syllabus",
        str(syllabus),
        "--note",
        str(module / NOTE),
        *extra,
    ]


def test_the_shipped_map_matches_the_notes_topics(module, syllabus_path):
    assert main(argv(module, syllabus_path, "--check")) == 0


GOOD = 'Querying → <a href="#querying">Querying</a>'
BROKEN = 'Querying → <a href="#gone">Querying</a>'


def test_check_fails_once_a_topic_is_renamed(module, syllabus_path, edit):
    edit(module, NOTE, 'id="querying"', 'id="joins-and-grouping"')
    assert main(argv(module, syllabus_path, "--check")) == 1


def test_write_repairs_the_map_and_is_idempotent(module, syllabus_path, edit):
    edit(module, NOTE, GOOD, BROKEN)
    assert main(argv(module, syllabus_path, "--write")) == 0
    once = (module / NOTE).read_text(encoding="utf-8")
    assert GOOD in once

    assert main(argv(module, syllabus_path, "--write")) == 0
    assert (module / NOTE).read_text(encoding="utf-8") == once


def test_write_leaves_the_rest_of_the_note_alone(module, syllabus_path, edit):
    before = (module / NOTE).read_text(encoding="utf-8")
    edit(module, NOTE, GOOD, BROKEN)
    main(argv(module, syllabus_path, "--write"))
    assert (module / NOTE).read_text(encoding="utf-8") == before


def test_an_outline_item_no_topic_covers_is_left_unlinked(module, syllabus_path, edit):
    edit(
        module.parent / "plan",
        syllabus_path.name,
        "2. Querying",
        "2. Querying\n3. Stored Procedures",
    )
    body = syllabus_map.render(syllabus_path.read_text(encoding="utf-8"), dom.parse(module / NOTE))

    assert "<li>Stored Procedures</li>" in body
    assert "Stored Procedures →" not in body


def test_the_map_links_only_to_topics(module, syllabus_path, edit):
    """`Module Map` shares a word with no outline item here, but a heading
    outside the topics must never be a target, whatever it shares."""
    edit(module, NOTE, "<h2>Module Map</h2>", "<h2>Querying Map</h2>")
    body = syllabus_map.render(syllabus_path.read_text(encoding="utf-8"), dom.parse(module / NOTE))
    assert 'href="#module-map"' not in body


def test_a_repaired_map_still_verifies(module, syllabus_path, edit, fired):
    edit(module, NOTE, GOOD, BROKEN)
    assert "MAT-D13" in fired(module)

    main(argv(module, syllabus_path, "--write"))
    assert fired(module) == set()


def test_a_note_without_a_map_gets_one_before_further_reading(module, syllabus_path):
    """The part is optional, so `--check` calls a missing map stale and
    `--write` adds it where the grammar puts it."""
    import re

    path = module / NOTE
    text = path.read_text(encoding="utf-8")
    path.write_text(
        re.sub(r'<section data-part="syllabus-map".*?</section>\n\n', "", text, flags=re.DOTALL),
        encoding="utf-8",
    )
    assert main(argv(module, syllabus_path, "--check")) == 1
    assert main(argv(module, syllabus_path, "--write")) == 0
    after = path.read_text(encoding="utf-8")
    assert after.index('data-part="syllabus-map"') < after.index('data-part="further-reading"')
    assert GOOD in after
    assert main(argv(module, syllabus_path, "--check")) == 0


def test_vietnamese_items_link_to_vietnamese_topics(module, syllabus_path, edit):
    """A Vietnamese syllable is short and accented: matching only long ASCII
    words found nothing to link."""
    edit(module, NOTE, "<h2>Relational Modelling</h2>", "<h2>Mô hình hoá quan hệ</h2>")
    edit(module, NOTE, "<h2>Querying</h2>", "<h2>Truy vấn dữ liệu</h2>")
    edit(
        module.parent / "plan", syllabus_path.name, "1. Relational Modelling", "1. Mô hình quan hệ"
    )
    edit(
        module.parent / "plan", syllabus_path.name, "2. Querying", "2. Truy vấn và gom nhóm dữ liệu"
    )
    body = syllabus_map.render(syllabus_path.read_text(encoding="utf-8"), dom.parse(module / NOTE))
    assert '<li>Mô hình quan hệ → <a href="#relational-modelling">' in body
    assert '<li>Truy vấn và gom nhóm dữ liệu → <a href="#querying">' in body
