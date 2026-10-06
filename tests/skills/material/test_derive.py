"""Deriving the appendix's syllabus map."""

from __future__ import annotations

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.skills.material.core import appendix

APPENDIX = "99_Appendix.md"


def argv(module, syllabus, *extra):
    return [
        "material",
        "derive",
        "appendix",
        "--syllabus",
        str(syllabus),
        "--dir",
        str(module),
        "--appendix",
        str(module / APPENDIX),
        *extra,
    ]


def test_the_shipped_appendix_matches_its_notes(module, syllabus_path):
    assert main(argv(module, syllabus_path, "--check")) == 0


def test_check_fails_once_a_heading_is_renamed(module, syllabus_path, edit):
    """The map's anchors are the only deep links in a module."""
    edit(module, "02_Querying.md", "# Querying\n", "# Querying Data\n")
    assert main(argv(module, syllabus_path, "--check")) == 1


def test_write_repairs_the_map_and_is_idempotent(module, syllabus_path, edit):
    edit(module, APPENDIX, "→ [02](02_Querying.md#querying)", "→ [02](02_Querying.md#gone)")
    assert main(argv(module, syllabus_path, "--write")) == 0
    once = (module / APPENDIX).read_text(encoding="utf-8")
    assert "#querying" in once

    assert main(argv(module, syllabus_path, "--write")) == 0
    assert (module / APPENDIX).read_text(encoding="utf-8") == once


def test_write_leaves_the_rest_of_the_appendix_alone(module, syllabus_path, edit):
    before = (module / APPENDIX).read_text(encoding="utf-8")
    edit(module, APPENDIX, "→ [02](02_Querying.md#querying)", "→ [02](02_Querying.md#gone)")
    main(argv(module, syllabus_path, "--write"))
    after = (module / APPENDIX).read_text(encoding="utf-8")

    assert after == before
    assert "## D. Glossary" in after


def test_an_outline_item_no_note_covers_is_left_unlinked(module, syllabus_path, edit):
    edit(
        module.parent / "plan",
        syllabus_path.name,
        "2. Querying",
        "2. Querying\n3. Stored Procedures",
    )
    body = appendix.render(syllabus_path.read_text(encoding="utf-8"), module)

    assert "- [ ] Stored Procedures" in body
    assert "Stored Procedures →" not in body


def test_a_repaired_appendix_still_verifies(module, syllabus_path, edit, fired):
    edit(module, APPENDIX, "→ [02](02_Querying.md#querying)", "→ [02](02_Querying.md#gone)")
    assert "MAT-D13" in fired(module)

    main(argv(module, syllabus_path, "--write"))
    assert fired(module) == set()


def test_write_needs_an_appendix(module, syllabus_path):
    with pytest.raises(UsageError, match="need --appendix"):
        main(
            [
                "material",
                "derive",
                "appendix",
                "--syllabus",
                str(syllabus_path),
                "--dir",
                str(module),
                "--write",
            ]
        )
