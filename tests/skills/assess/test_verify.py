"""Structural verification: the real artifacts pass, and defects are caught.

Both halves matter. A verifier that passes everything is worthless, and one that
fails the artifacts already in production is worse than worthless.
"""

from __future__ import annotations

import csv

import pytest

from fsa_trainer_skills.skills.assess.core import levels
from fsa_trainer_skills.skills.assess.core.verify import CheckResult, long_form, question_set
from fsa_trainer_skills.skills.assess.core.verify.common import DEFAULT_TIME_MAP

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
