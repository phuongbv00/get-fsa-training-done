"""Deriving the tables that must not be typed by hand.

The point of deriving is that the derived file cannot disagree with its source.
So these check the arithmetic, that writing twice changes nothing, and that a
document this produces passes the same rules `verify` applies to a hand-written
one.
"""

from __future__ import annotations

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import FsaTrainerSkillsError, UsageError
from get_fsa_training_done.skills.program.core import csvio
from get_fsa_training_done.skills.program.core import program as program_mod
from get_fsa_training_done.skills.program.core.derive import allocation, skeleton

DBF = "curriculum/syllabi/AA_FR_TT_DBF_Syllabus.md"
DBF_PLAN = "curriculum/syllabi/AA_FR_TT_DBF_ScheduleDetail.csv"
CURRICULUM = "curriculum/AA_FR_TT_DEMO_TrainingProgramCurriculum.md"


def rows_of(mini):
    return csvio.read_table(mini / DBF_PLAN).rows


# --- Time allocation ------------------------------------------------------


def test_shares_are_minutes_over_total(mini):
    shares = allocation.shares(rows_of(mini))
    # 150 of 720 minutes are lectures.
    assert shares["Concept/Lecture"] == 20.83
    assert shares["Assignment/Lab"] == 41.67
    assert shares["Seminar/Workshop"] == 0.0
    assert set(shares) == set(allocation.DELIVERY_TYPES)


def test_the_shipped_example_already_matches_its_session_plan(mini):
    """`derive --check` and the example must agree, or one of them is wrong."""
    assert (
        main(
            [
                "program",
                "derive",
                "allocation",
                "--schedule",
                str(mini / DBF_PLAN),
                "--syllabus",
                str(mini / DBF),
                "--check",
            ]
        )
        == 0
    )


def test_check_fails_on_a_share_that_has_drifted(mini, edit):
    edit(mini, DBF, "| Concept/Lecture | 20.83% |", "| Concept/Lecture | 21.00% |")
    assert (
        main(
            [
                "program",
                "derive",
                "allocation",
                "--schedule",
                str(mini / DBF_PLAN),
                "--syllabus",
                str(mini / DBF),
                "--check",
            ]
        )
        == 1
    )


def test_write_repairs_a_drifted_share_and_is_idempotent(mini, edit):
    edit(mini, DBF, "| Concept/Lecture | 20.83% |", "| Concept/Lecture | 21.00% |")
    argv = [
        "program",
        "derive",
        "allocation",
        "--schedule",
        str(mini / DBF_PLAN),
        "--syllabus",
        str(mini / DBF),
        "--write",
    ]
    assert main(argv) == 0
    once = (mini / DBF).read_text(encoding="utf-8")
    assert "| Concept/Lecture | 20.83% |" in once

    assert main(argv) == 0
    assert (mini / DBF).read_text(encoding="utf-8") == once


def test_write_touches_only_section_eight(mini, edit):
    before = (mini / DBF).read_text(encoding="utf-8")
    edit(mini, DBF, "| Concept/Lecture | 20.83% |", "| Concept/Lecture | 21.00% |")
    main(
        [
            "program",
            "derive",
            "allocation",
            "--schedule",
            str(mini / DBF_PLAN),
            "--syllabus",
            str(mini / DBF),
            "--write",
        ]
    )
    assert (mini / DBF).read_text(encoding="utf-8") == before


def test_a_derived_syllabus_passes_verification(mini, edit, fired):
    edit(mini, DBF, "| Exam | 20.83% |", "| Exam | 19.00% |")
    assert "PRG-S09" in fired(mini)

    main(
        [
            "program",
            "derive",
            "allocation",
            "--schedule",
            str(mini / DBF_PLAN),
            "--syllabus",
            str(mini / DBF),
            "--write",
        ]
    )
    assert fired(mini) == set()


def test_days_are_restated_only_when_a_training_day_is_given(mini):
    body = allocation.render(rows_of(mini), days=None)
    assert "**Days:**" not in body
    assert allocation.days_for(rows_of(mini), 240) == 3


def test_a_plan_that_is_not_whole_days_is_an_error(mini):
    with pytest.raises(UsageError, match="whole number"):
        allocation.days_for(rows_of(mini), 500)


def test_write_needs_a_syllabus(mini):
    with pytest.raises(UsageError, match="need --syllabus"):
        main(["program", "derive", "allocation", "--schedule", str(mini / DBF_PLAN), "--write"])


# --- Programme skeletons --------------------------------------------------


def test_week_and_day_columns_follow_from_the_training_days():
    """Five teaching days a week, Monday to Sunday columns, stopping on the
    last teaching day rather than padding a trailing weekend."""
    assert (skeleton.week_count(70), skeleton.day_column_count(70)) == (14, 96)
    assert (skeleton.week_count(5), skeleton.day_column_count(5)) == (1, 5)
    assert (skeleton.week_count(10), skeleton.day_column_count(10)) == (2, 12)


def test_the_skeletons_have_the_headers_verify_requires(mini, tmp_path):
    out = tmp_path / "out"
    assert (
        main(
            [
                "program",
                "derive",
                "skeleton",
                "--curriculum",
                str(mini / CURRICULUM),
                "--out-dir",
                str(out),
            ]
        )
        == 0
    )

    written = sorted(p.name for p in out.glob("*.csv"))
    assert written == [
        "AA_FR_TT_DEMO_DetailedSchedule.csv",
        "AA_FR_TT_DEMO_MasterSchedule.csv",
        "AA_FR_TT_DEMO_OSTModuleMapping.csv",
        "AA_FR_TT_DEMO_TopicList.csv",
    ]
    for name in written:
        generated = csvio.read_table(out / name)
        shipped = csvio.read_table(mini / "curriculum" / name)
        assert generated.headers == shipped.headers, name


def test_each_skeleton_has_one_row_per_module_in_order(mini, tmp_path):
    out = tmp_path / "out"
    main(
        [
            "program",
            "derive",
            "skeleton",
            "--curriculum",
            str(mini / CURRICULUM),
            "--out-dir",
            str(out),
            "--kind",
            "master",
        ]
    )
    table = csvio.read_table(out / "AA_FR_TT_DEMO_MasterSchedule.csv")
    program = program_mod.parse(mini / CURRICULUM)
    assert table.column("Module") == list(program.codes)
    # The assessment week is a judgement call, so it is left blank.
    assert {row["W1"] for row in table.rows} == {""}


def test_skeleton_refuses_to_overwrite_without_force(mini, tmp_path):
    out = tmp_path / "out"
    argv = [
        "program",
        "derive",
        "skeleton",
        "--curriculum",
        str(mini / CURRICULUM),
        "--out-dir",
        str(out),
        "--kind",
        "topic-list",
    ]
    assert main(argv) == 0
    with pytest.raises(FsaTrainerSkillsError, match="already exists"):
        main(argv)
    assert main([*argv, "--force"]) == 0
