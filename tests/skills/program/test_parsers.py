"""Reading the curriculum and syllabus documents.

The documents are hand-authored against a section order the vendor workbook
fixes, so these cover the shapes that actually appear — including the two
Markdown-escaping traps the real corpus contains.
"""

from __future__ import annotations

import pytest

from fsa_trainer_skills.errors import UsageError
from fsa_trainer_skills.skills.program.core import mdtable
from fsa_trainer_skills.skills.program.core import program as program_mod

CURRICULUM = """# Java Full-Stack — Fresher

## Training Program Curriculum

**For Roles:** Junior Java Developer

### 1. The Modules

| # | Module Name | Code | Duration (hrs) | Duration (days) | Description |
|---:|---|---|---:|---:|---|
| 1 | Foundations | `AA_FR_TT_FND` | 20 | 5 | First. |
| 2 | Databases | `AA_FR_TT_DBF` | 40 | 10 | Second. |
| | **TOTAL** | | **60** | **15** | |

### 2. Schedule Design

Prose.

### 3. Mapping

Prose.

### 4. Topic List

Prose.
"""


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# --- Markdown primitives -------------------------------------------------


def test_strip_md_removes_the_emphasis_authors_use():
    # The same value is bold in a TOTAL row and plain in a data row; they have
    # to compare equal or the totals never reconcile.
    assert mdtable.strip_md("**TOTAL**") == "TOTAL"
    assert mdtable.strip_md("`AA_FR_TT_FND`") == "AA_FR_TT_FND"
    assert mdtable.strip_md("  spaced  ") == "spaced"


def test_a_literal_asterisk_in_a_header_cell_survives():
    """`A*, M, D` is a real header in the record-of-changes table."""
    rows = mdtable.md_table_rows("| Date | Changes | A*, M, D | Contents | Version |")
    assert rows == [["Date", "Changes", "A*, M, D", "Contents", "Version"]]


def test_the_escaped_change_log_preamble_is_not_a_table_row():
    """`\\*A - Added · M - Modified · D - Deleted` sits above the table."""
    text = "\\*A - Added · M - Modified · D - Deleted\n\n| Date | Changes |\n|---|---|\n| x | y |\n"
    assert mdtable.md_table_rows(text) == [["Date", "Changes"], ["x", "y"]]


def test_separator_rows_are_dropped():
    rows = mdtable.md_table_rows("| A | B |\n|:---|---:|\n| 1 | 2 |")
    assert rows == [["A", "B"], ["1", "2"]]


def test_a_missing_section_reads_empty_rather_than_raising():
    assert mdtable.section("# Title\n", "### 8. Time Allocation") == ""


# --- Programme curriculum -------------------------------------------------


def test_the_module_table_and_totals_parse(tmp_path):
    program = program_mod.parse(write(tmp_path, "c.md", CURRICULUM))

    assert program.title == "Java Full-Stack — Fresher"
    assert program.role == "Junior Java Developer"
    assert program.codes == ("AA_FR_TT_FND", "AA_FR_TT_DBF")
    assert (program.total_hours, program.total_days) == (60, 15)
    assert [m.hours for m in program.modules] == [20, 40]


def test_the_length_of_a_training_day_is_derived_not_assumed(tmp_path):
    """The reference pipeline hardcoded 240 minutes and a 16800-minute total.

    Both are this one number in disguise, and a programme that runs full days
    must not be measured against someone else's timetable.
    """
    program = program_mod.parse(write(tmp_path, "c.md", CURRICULUM))
    assert program.minutes_per_day == 240

    full_days = CURRICULUM.replace("**60**", "**120**")
    assert program_mod.parse(write(tmp_path, "d.md", full_days)).minutes_per_day == 480


def test_a_training_day_that_is_not_whole_minutes_is_an_error(tmp_path):
    odd = CURRICULUM.replace("**15**", "**7**")
    program = program_mod.parse(write(tmp_path, "c.md", odd))
    with pytest.raises(UsageError, match="not a whole number"):
        _ = program.minutes_per_day


def test_a_missing_module_table_yields_no_modules(tmp_path):
    program = program_mod.parse(write(tmp_path, "c.md", "# Title\n\nNothing here.\n"))
    assert program.modules == ()
    assert program.total_hours == 0
