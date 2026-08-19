"""Structural verification: the real artifacts pass, and defects are caught.

Both halves matter. A verifier that passes everything is worthless, and one that
fails the artifacts already in production is worse than worthless.
"""

from __future__ import annotations

import csv

import pytest

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
