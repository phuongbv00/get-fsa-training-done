"""Reading a topic syllabus.

The export contract fixes the section order — the vendor workbook writes each
section to a hard-coded cell range — so a missing or renamed heading has to
surface rather than silently yielding an empty table.
"""

from __future__ import annotations

import pytest

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.program.core import syllabus as syllabus_mod

SYLLABUS = """# AA_FR_TT_DBF — Database Foundations

## Syllabus

| # | Field | Value |
|---|---|---|
| 1 | **Technical Group** | Common |
| 2 | **Topic Name** | Database Foundations |
| 3 | **Topic Code** | `AA_FR_TT_DBF` |
| 4 | **Version** | 2026.4 |
| 5 | **Training Audience** | Fresher — TT track |

### 6. Course Objectives

Intro prose.

| Name | Code | Description |
|---|---|---|
| Modelling | DBF-K1 | Convert a domain description into a schema |
| Querying | DBF-K2 | Write correct CRUD and joins |

After completing the topic, trainees will be able to:

- Model entities and normalize to third normal form.
- Write queries that return correct results.

### 7. Topic Outline

1. Relational Modelling
2. Final Assessments

### 8. Time Allocation

**Days:** 5

| Delivery Type | Share |
|---|---:|
| Concept/Lecture | 15.00% |
| Assignment/Lab | 52.50% |
| Guides/Review | 7.50% |
| Seminar/Workshop | 0.00% |
| Class Meeting | 0.00% |
| Test/Quiz | 5.00% |
| Exam | 20.00% |
| **Total** | **100.00%** |

### 9. Training Materials & Environments

| Item | Value |
|---|---|
| Text book | N/A |
| References | Official documentation |
| Technical requirements | A database engine |

### 10. Assessment Scheme

| Item | Count | Weight | Notes |
|---|---:|---:|---|
| Quiz | 2 | 10% | Two quizzes |
| Assignment | 1 | 20% | One long assignment |
| Final Theory Exam | 1 | 30% | Open-ended |
| Final Practice Exam | 1 | 40% | Bounded tasks |
| **Pass Criteria** | **6** | | **Topic GPA at least 6/10.** |

### 11. Training Delivery Principles

| Item | Value |
|---|---|
| **Trainees** | Qualified entry test |
| **Re-Test** | Each trainee may retake a failed final exam **1** time |

## Author and Rec of Changes

### AUTHORSHIP

| Role | Name | Account | Unit | Notes |
|---|---|---|---|---|
| Creator | Phuong Bui Viet | PhuongBV3 | FSA.LS.N | |
| Reviewer | | | | |
| Approver | | | | |

### RECORD OF CHANGES

\\*A - Added · M - Modified · D - Deleted

| Date | Changes | A*, M, D | Contents | Version |
|---|---|:---:|---|---:|
| 21/08/2026 | Create new | A | Create syllabus | 2026.4 |
"""


@pytest.fixture
def syllabus(tmp_path):
    path = tmp_path / "AA_FR_TT_DBF_Syllabus.md"
    path.write_text(SYLLABUS, encoding="utf-8")
    return syllabus_mod.parse(path)


def test_the_heading_and_identity_fields_parse(syllabus):
    assert syllabus.code == "AA_FR_TT_DBF"
    assert syllabus.title == "Database Foundations"
    assert syllabus.fields[3] == "AA_FR_TT_DBF"
    assert syllabus.fields[2] == syllabus.title


def test_objectives_outcomes_and_outline_parse(syllabus):
    assert [o.code for o in syllabus.objectives] == ["DBF-K1", "DBF-K2"]
    assert len(syllabus.outcomes) == 2
    assert syllabus.outline == ("Relational Modelling", "Final Assessments")


def test_time_allocation_parses_days_and_every_delivery_type(syllabus):
    assert syllabus.days == 5
    shares = syllabus.shares()
    assert shares["Assignment/Lab"] == 52.5
    # The bold Total row is not a delivery type and must not become one.
    assert "Total" not in shares
    assert len(shares) == 7


def test_pass_criteria_keeps_a_blank_weight(syllabus):
    """A blank weight is required, and 0 would be a different claim."""
    pass_row = syllabus.assessments[-1]
    assert pass_row.item == "Pass Criteria"
    assert pass_row.count == 6
    assert pass_row.weight is None


def test_weights_parse_as_numbers(syllabus):
    assert [a.weight for a in syllabus.assessments[:-1]] == [10.0, 20.0, 30.0, 40.0]


def test_authorship_and_the_change_log_parse(syllabus):
    """The change table's header carries a literal asterisk, and an escaped
    preamble line sits above it — neither may be read as data."""
    creator = syllabus.author("Creator")
    assert (creator.name, creator.account, creator.unit) == (
        "Phuong Bui Viet",
        "PhuongBV3",
        "FSA.LS.N",
    )
    reviewer = syllabus.author("Reviewer")
    assert not any((reviewer.name, reviewer.account, reviewer.unit))
    assert len(syllabus.changes) == 1
    assert syllabus.changes[0].action == "A"


def test_a_renamed_section_yields_nothing_rather_than_wrong_data(tmp_path):
    """The heading is the contract. A near-miss must not half-parse."""
    path = tmp_path / "s.md"
    path.write_text(SYLLABUS.replace("### 8. Time Allocation", "### 8. Time allocation"), "utf-8")

    parsed = syllabus_mod.parse(path)

    assert parsed.days == 0
    assert parsed.time_rows == ()


def test_a_missing_file_is_a_usage_error(tmp_path):
    with pytest.raises(UsageError, match="syllabus not found"):
        syllabus_mod.parse(tmp_path / "nope.md")
