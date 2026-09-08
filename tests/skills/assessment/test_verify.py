"""Structural verification: the real artifacts pass, and defects are caught.

Both halves matter. A verifier that passes everything is worthless, and one that
fails the artifacts already in production is worse than worthless.
"""

from __future__ import annotations

import csv

import pytest

from fsa_trainer_skills import levels
from fsa_trainer_skills.skills.assessment.core.verify import (
    CheckResult,
    capstone,
    long_form,
    question_set,
)
from fsa_trainer_skills.skills.assessment.core.verify.common import DEFAULT_TIME_MAP

from .conftest import FIXTURES


def verify_long_form(brief, rubric, **kwargs):
    result = CheckResult()
    long_form.verify(
        assessment_type=kwargs.pop("assessment_type", "practice_exam"),
        brief_path=str(brief),
        rubric_path=str(rubric),
        pdf_path=kwargs.pop("pdf_path", None),
        max_pages=kwargs.pop("max_pages", None),
        result=result,
        level=kwargs.pop("level", None),
    )
    return result


def verify_capstone(brief, spec, rubric, **kwargs):
    """The full capstone pass: the shared long-form checks, then the capstone ones."""
    result = CheckResult()
    long_form.verify(
        assessment_type="capstone_project",
        brief_path=str(brief),
        rubric_path=str(rubric),
        pdf_path=None,
        max_pages=None,
        result=result,
        level=kwargs.pop("level", None),
    )
    capstone.verify(
        brief_path=str(brief),
        spec_path=str(spec),
        rubric_path=str(rubric),
        result=result,
    )
    return result


def verify_question_set(master, **kwargs):
    result = CheckResult()
    question_set.verify(
        master_path=str(master),
        blooket_path=kwargs.get("blooket"),
        coderbyte_path=kwargs.get("coderbyte"),
        time_map=kwargs.get("time_map", dict(DEFAULT_TIME_MAP)),
        expect_count=kwargs.get("expect_count"),
        result=result,
        level=kwargs.get("level"),
    )
    return result


# --------------------------------------------------------------------------- #
# The real artifacts must pass
# --------------------------------------------------------------------------- #


def test_canonical_brief_and_rubric_pass(long_form_pair):
    result = verify_long_form(*long_form_pair)
    assert result.errors == []


def test_canonical_capstone_trio_passes(capstone_trio):
    result = verify_capstone(*capstone_trio)
    assert result.errors == []
    assert result.warnings == []


def test_real_quiz_master_and_blooket_pass():
    result = verify_question_set(
        FIXTURES / "question_set" / "quiz_master.csv",
        blooket=str(FIXTURES / "question_set" / "quiz_blooket.csv"),
    )
    assert result.errors == []


def test_real_theory_master_and_coderbyte_pass():
    result = verify_question_set(
        FIXTURES / "question_set" / "theory_master.csv",
        coderbyte=str(FIXTURES / "question_set" / "theory_coderbyte.json"),
    )
    assert result.errors == []


# --------------------------------------------------------------------------- #
# Defects must be caught
# --------------------------------------------------------------------------- #


def test_retired_brief_sections_are_rejected(long_form_pair, tmp_path):
    brief, rubric = long_form_pair
    brief.write_text(
        brief.read_text(encoding="utf-8").replace(
            "## 1. Problem Statement", "## 1. Context & Objective"
        ),
        encoding="utf-8",
    )
    result = verify_long_form(brief, rubric)
    assert any("retired section" in error for error in result.errors)


def test_weight_mismatch_between_brief_and_rubric_is_caught(long_form_pair):
    brief, rubric = long_form_pair
    brief.write_text(
        brief.read_text(encoding="utf-8").replace("(15%)", "(20%)", 1), encoding="utf-8"
    )
    result = verify_long_form(brief, rubric)
    assert any("weight" in error.lower() for error in result.errors)


def test_score_sheet_rows_do_not_double_count_tasks(long_form_pair):
    """A rubric whose score sheet puts the id in its own cell must not
    double-count the task list. Parsing the whole document instead of the fixed
    task list section did exactly that."""
    brief, rubric = long_form_pair
    text = rubric.read_text(encoding="utf-8")
    # Rewrite the score sheet into the id-in-its-own-cell form, which is what
    # trips a whole-document parse.
    lines = []
    in_sheet = False
    for line in text.splitlines():
        if line.startswith("## 6. Score sheet"):
            in_sheet = True
        if in_sheet and line.startswith("| T"):
            parts = [p.strip() for p in line.strip("|").split("|")]
            task_id = parts[0].split()[0]
            lines.append(f"| {task_id} | | {parts[2]} | |")
            continue
        lines.append(line)
    rubric.write_text("\n".join(lines), encoding="utf-8")

    result = verify_long_form(brief, rubric)
    assert not any("Task count mismatch" in error for error in result.errors)
    assert not any("weights sum to 200" in error for error in result.errors)


def test_backtick_in_a_question_is_rejected(tmp_path, quiz_master_rows):
    rows = quiz_master_rows
    rows[1][4] = "What does `List` do?"
    path = tmp_path / "q.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    result = verify_question_set(path)
    assert any("backtick" in error for error in result.errors)


def test_raw_generic_is_rejected(tmp_path, quiz_master_rows):
    rows = quiz_master_rows
    rows[1][4] = "What does List<String> declare?"
    path = tmp_path / "q.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    result = verify_question_set(path)
    assert any("angle bracket" in error for error in result.errors)


@pytest.mark.parametrize(
    "text",
    ["user -> user.isActive()", "score >= 5", "Country <> 'Germany'"],
    ids=["lambda", "comparison", "sql-not-equal"],
)
def test_operators_are_not_mistaken_for_tags(tmp_path, quiz_master_rows, text):
    rows = quiz_master_rows
    rows[1][4] = f"What does {text} evaluate to?"
    path = tmp_path / "q.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    result = verify_question_set(path)
    assert not any("angle bracket" in error for error in result.errors)


def test_wrong_time_limit_is_caught(tmp_path, quiz_master_rows):
    rows = quiz_master_rows
    rows[1][10] = "999"
    path = tmp_path / "q.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    result = verify_question_set(path)
    assert any("time limit" in error for error in result.errors)
    assert any("maximum" in error for error in result.errors)


# --------------------------------------------------------------------------- #
# Level calibration
#
# `--level`/`--band` used to be parsed and thrown away. These pin the two
# things that must stay true: drift is reported, and it is only ever a warning.
# --------------------------------------------------------------------------- #


def build_master(tmp_path, template, mixes):
    """A master CSV whose rows carry the given (Bloom, Difficulty) pairs."""
    header, sample = template[0], template[1]
    rows = [header]
    for index, (bloom, difficulty) in enumerate(mixes, start=1):
        row = list(sample)
        row[0] = str(index)
        row[2] = bloom
        row[3] = difficulty
        row[4] = f"Question {index}?"
        row[10] = DEFAULT_TIME_MAP[difficulty]
        rows.append(row)
    path = tmp_path / "master.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    return path


def test_level_calibration_is_silent_when_the_mix_matches(tmp_path, quiz_master_rows):
    # CPL over 10 questions: Remember 3, Understand 4, Apply 3 / Easy 5, Medium 4, Hard 1.
    blooms = ["Remember"] * 3 + ["Understand"] * 4 + ["Apply"] * 3
    difficulties = ["Easy"] * 5 + ["Medium"] * 4 + ["Hard"]
    master = build_master(tmp_path, quiz_master_rows, list(zip(blooms, difficulties)))
    result = verify_question_set(master, level=levels.resolve("CPL"))
    assert result.ok
    assert not any("mix differs" in warning for warning in result.warnings)


def test_level_calibration_warns_but_never_fails(tmp_path, quiz_master_rows):
    # All Remember/Easy is nothing like UP_SKILL (mid), which wants Apply/Analyze.
    master = build_master(tmp_path, quiz_master_rows, [("Remember", "Easy")] * 10)
    result = verify_question_set(master, level=levels.resolve("UP_SKILL", "mid"))
    assert result.ok, "calibration drift must never fail the run"
    assert any("Bloom mix differs" in warning for warning in result.warnings)
    assert any("Difficulty mix differs" in warning for warning in result.warnings)


def test_no_level_means_no_calibration_warnings(tmp_path, quiz_master_rows):
    master = build_master(tmp_path, quiz_master_rows, [("Remember", "Easy")] * 10)
    result = verify_question_set(master)
    assert not any("mix differs" in warning for warning in result.warnings)


def test_one_question_of_drift_is_tolerated(tmp_path, quiz_master_rows):
    # CPL over 10, with one Understand traded for a Remember: every bucket is
    # within a single question of target, so nothing is worth saying.
    blooms = ["Remember"] * 4 + ["Understand"] * 3 + ["Apply"] * 3
    difficulties = ["Easy"] * 5 + ["Medium"] * 4 + ["Hard"]
    master = build_master(tmp_path, quiz_master_rows, list(zip(blooms, difficulties)))
    result = verify_question_set(master, level=levels.resolve("CPL"))
    assert not any("mix differs" in warning for warning in result.warnings)


def test_task_count_outside_the_level_range_warns(long_form_pair):
    brief, rubric = long_form_pair
    # The canonical pair has five tasks; CPL wants 3-4.
    result = verify_long_form(brief, rubric, level=levels.resolve("CPL"))
    assert result.ok, "calibration drift must never fail the run"
    assert any("CPL suggests 3-4" in warning for warning in result.warnings)


def test_task_count_inside_the_level_range_is_silent(long_form_pair):
    brief, rubric = long_form_pair
    # Five tasks sits inside UP_SKILL (senior)'s 3-5.
    result = verify_long_form(brief, rubric, level=levels.resolve("UP_SKILL", "senior"))
    assert not any("suggests" in warning for warning in result.warnings)


# --------------------------------------------------------------------------- #
# Capstone sprint checkpoints
# --------------------------------------------------------------------------- #


def test_capstone_task_count_is_not_calibrated_against_the_level(capstone_trio):
    """Seven tasks is the programme's shape, not drift from FR's 4-6."""
    result = verify_capstone(*capstone_trio, level=levels.resolve("FR"))
    assert not any("suggests" in warning for warning in result.warnings)


def test_missing_sprint_table_is_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    text = spec.read_text(encoding="utf-8")
    start = text.index("| Sprint |")
    end = text.index("## Sprint checkpoint")
    spec.write_text(text[:start] + text[end:], encoding="utf-8")
    result = verify_capstone(brief, spec, rubric)
    assert any("no sprint table" in error for error in result.errors)


def test_a_deliverable_in_no_sprint_is_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("| D01, D02 |", "| D01 |"),
        encoding="utf-8",
    )
    result = verify_capstone(brief, spec, rubric)
    assert any("No sprint is responsible for D02" in error for error in result.errors)


def test_a_deliverable_in_two_sprints_is_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("| D03 |", "| D02, D03 |"),
        encoding="utf-8",
    )
    result = verify_capstone(brief, spec, rubric)
    assert any("D02 is due in sprints 1, 2" in error for error in result.errors)


def test_overlapping_sprint_windows_are_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("| 2 | 2026-09-15 |", "| 2 | 2026-09-10 |"),
        encoding="utf-8",
    )
    result = verify_capstone(brief, spec, rubric)
    assert any("on or before Sprint 1 ends" in error for error in result.errors)


def test_a_non_iso_sprint_date_is_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("| 1 | 2026-09-01 |", "| 1 | 01/09/2026 |"),
        encoding="utf-8",
    )
    result = verify_capstone(brief, spec, rubric)
    assert any("is not ISO 8601" in error for error in result.errors)


def test_a_brief_referring_to_a_sprint_that_does_not_exist_is_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    brief.write_text(
        brief.read_text(encoding="utf-8").replace("Due in Sprint 2.", "Due in Sprint 4."),
        encoding="utf-8",
    )
    result = verify_capstone(brief, spec, rubric)
    assert any("Brief refers to Sprint 4" in error for error in result.errors)


def test_a_lowercase_sprint_duration_is_not_a_sprint_reference(capstone_trio):
    """'each sprint 2 weeks long' names a length, not Sprint 2."""
    brief, spec, rubric = capstone_trio
    brief.write_text(
        brief.read_text(encoding="utf-8") + "\nEach sprint 9 days long.\n", encoding="utf-8"
    )
    result = verify_capstone(brief, spec, rubric)
    assert not any("Sprint 9" in error for error in result.errors)


def test_a_missing_checkpoint_section_is_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("## Sprint checkpoint", "## Notes"),
        encoding="utf-8",
    )
    result = verify_capstone(brief, spec, rubric)
    assert any("no '## Sprint checkpoint' section" in error for error in result.errors)


def test_an_undefined_gate_is_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    # Every mention, not just the heading — G4 is cross-referenced from G1's body.
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("G4", "GX"),
        encoding="utf-8",
    )
    result = verify_capstone(brief, spec, rubric)
    assert any("does not define gate G4" in error for error in result.errors)


def test_a_multi_sprint_rubric_without_a_sprint_task_is_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    for path in (brief, rubric):
        path.write_text(
            path.read_text(encoding="utf-8").replace("Sprint Process", "Team Collaboration"),
            encoding="utf-8",
        )
    result = verify_capstone(brief, spec, rubric)
    assert any("no sprint-process task" in error for error in result.errors)


def test_one_task_scoring_both_process_and_individual_is_caught(capstone_trio):
    brief, spec, rubric = capstone_trio
    for path in (brief, rubric):
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "Sprint Process", "Sprint Process and individual"
            ),
            encoding="utf-8",
        )
    result = verify_capstone(brief, spec, rubric)
    assert any("scores both the team's sprint process" in error for error in result.errors)


def test_gates_with_no_cap_at_all_is_an_error(capstone_trio):
    brief, spec, rubric = capstone_trio
    text = rubric.read_text(encoding="utf-8")
    start = text.index("## 4. Caps and Deductions")
    end = text.index("## 5. Common point-loss reasons")
    rubric.write_text(
        text[:start] + "## 4. Caps and Deductions\n\nNothing is capped.\n\n" + text[end:],
        encoding="utf-8",
    )
    result = verify_capstone(brief, spec, rubric)
    assert any("never names a sprint gate" in error for error in result.errors)


def test_a_gate_with_no_cap_warns_but_does_not_fail(capstone_trio):
    brief, spec, rubric = capstone_trio
    rubric.write_text(
        rubric.read_text(encoding="utf-8").replace(
            "| G4 missing in any sprint | T7 capped at 7.0 for every member of that team |\n", ""
        ),
        encoding="utf-8",
    )
    result = verify_capstone(brief, spec, rubric)
    assert result.errors == []
    assert any("names no consequence for G4" in warning for warning in result.warnings)
