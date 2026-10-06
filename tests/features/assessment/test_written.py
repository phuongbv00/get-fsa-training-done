"""The written form of a quiz or theory exam: a brief of open-ended questions,
a rubric, and the answer template the candidate fills in.

The fixtures are a real theory exam and a real written quiz, so the checks are
held to artifacts that were actually sat.
"""

from __future__ import annotations

import shutil

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.assessment.core.verify import (
    CheckResult,
    answer_template,
    long_form,
)
from get_fsa_training_done.features.common import levels

from .conftest import FIXTURES

WRITTEN = FIXTURES / "written"
THEORY = WRITTEN / "jcf_theory_exam_01.md"
THEORY_RUBRIC = WRITTEN / "jcf_theory_exam_01_rubric.md"
TEMPLATE = WRITTEN / "jcf_theory_exam_01_answer_template.md"


def check_template(brief, template, assessment_type="theory_exam"):
    result = CheckResult()
    answer_template.verify(
        assessment_type=assessment_type,
        brief_path=str(brief),
        template_path=str(template),
        result=result,
    )
    return result


@pytest.mark.parametrize(
    ("assessment_type", "stem"),
    [("theory_exam", "jcf_theory_exam_01"), ("quiz", "dbf_quiz_02")],
)
def test_the_real_written_artifacts_pass(assessment_type, stem):
    result = CheckResult()
    long_form.verify(
        assessment_type=assessment_type,
        brief_path=str(WRITTEN / f"{stem}.md"),
        rubric_path=str(WRITTEN / f"{stem}_rubric.md"),
        pdf_path=None,
        max_pages=10,
        result=result,
        level=levels.resolve("FR"),
    )
    assert result.errors == []
    # Five questions per topic is not a build task count; the level's range
    # does not apply.
    assert not any("tasks;" in warning for warning in result.warnings)


def test_a_translated_brief_is_checked_against_the_english_rubric(tmp_path):
    vn = tmp_path / "jcf_theory_exam_01_vn.md"
    vn.write_text(THEORY.read_text(encoding="utf-8"), encoding="utf-8")
    result = CheckResult()
    long_form.verify(
        assessment_type="theory_exam",
        brief_path=str(vn),
        rubric_path=str(THEORY_RUBRIC),
        pdf_path=None,
        max_pages=10,
        result=result,
    )
    assert result.errors == []


def test_the_real_answer_template_passes():
    result = check_template(THEORY, TEMPLATE)
    assert result.errors == [] and result.warnings == []


def test_a_template_that_quotes_a_question_fails(tmp_path):
    leaky = tmp_path / TEMPLATE.name
    question = (
        "How does a `HashMap` work when you `put` and `get` an entry? What happens if "
        "`equals()` and `hashCode()` break their contract?"
    )
    leaky.write_text(
        TEMPLATE.read_text(encoding="utf-8").replace("**Q12.**", f"**Q12.** {question}"),
        encoding="utf-8",
    )
    result = check_template(THEORY, leaky)
    assert any("repeats the brief's question text" in error for error in result.errors)


def test_a_template_missing_a_question_slot_fails(tmp_path):
    short = tmp_path / TEMPLATE.name
    short.write_text(TEMPLATE.read_text(encoding="utf-8").replace("**Q20.**", ""), encoding="utf-8")
    result = check_template(THEORY, short)
    assert any("T4 has slots" in error for error in result.errors)


def test_a_template_with_a_renamed_task_fails(tmp_path):
    renamed = tmp_path / TEMPLATE.name
    renamed.write_text(
        TEMPLATE.read_text(encoding="utf-8").replace(
            "## Task 3 - Collections and Streams", "## Task 3 - Collections"
        ),
        encoding="utf-8",
    )
    result = check_template(THEORY, renamed)
    assert any("does not match brief" in error for error in result.errors)


def test_a_theory_template_needs_the_candidate_line(tmp_path):
    anonymous = tmp_path / TEMPLATE.name
    anonymous.write_text(
        TEMPLATE.read_text(encoding="utf-8").replace(answer_template.CANDIDATE_LINE, ""),
        encoding="utf-8",
    )
    result = check_template(THEORY, anonymous)
    assert any("Candidate" in error for error in result.errors)


def test_a_translated_template_keeps_vn_last():
    brief = THEORY.with_name("jcf_theory_exam_01_vn.md")
    good = THEORY.with_name("jcf_theory_exam_01_answer_template_vn.md")
    bad = THEORY.with_name("jcf_theory_exam_01_vn_answer_template.md")
    assert answer_template.name_matches(brief, good, "theory_exam")
    assert not answer_template.name_matches(brief, bad, "theory_exam")


def test_slots_out_of_order_fail(tmp_path):
    swapped = tmp_path / TEMPLATE.name
    text = TEMPLATE.read_text(encoding="utf-8")
    swapped.write_text(
        text.replace("**Q1.**", "**QX.**")
        .replace("**Q2.**", "**Q1.**")
        .replace("**QX.**", "**Q2.**"),
        encoding="utf-8",
    )
    result = check_template(THEORY, swapped)
    assert any("T1 has slots Q2, Q1" in error for error in result.errors)


def test_every_slot_under_the_last_task_fails(tmp_path):
    """The old check compared one set of numbers for the whole file."""
    import re

    text = TEMPLATE.read_text(encoding="utf-8")
    slots = re.findall(r"\*\*Q\d+\.\*\*\n\n<your answer>\n\n", text)
    stripped = re.sub(r"\*\*Q\d+\.\*\*\n\n<your answer>\n\n", "", text)
    moved = tmp_path / TEMPLATE.name
    moved.write_text(stripped.rstrip() + "\n\n" + "".join(slots), encoding="utf-8")
    assert check_template(THEORY, moved).errors


def test_a_practice_exam_worksheet_may_serve_one_task(tmp_path):
    brief = FIXTURES / "long_form" / "sbf_practice_exam_02.md"
    task_two = next(
        line
        for line in brief.read_text(encoding="utf-8").splitlines()
        if line.startswith("### Task 2 ")
    )
    name = task_two.removeprefix("### ").rsplit(" (", 1)[0]
    sheet = tmp_path / "sbf_practice_exam_02_design_template.md"
    sheet.write_text(f"# Worksheet\n\n## {name}\n\n| A | B |\n|---|---|\n", encoding="utf-8")
    result = check_template(brief, sheet, assessment_type="practice_exam")
    assert result.errors == [] and result.warnings == []

    sheet.write_text("# Worksheet\n\n## Task 2 - Something Else\n", encoding="utf-8")
    assert check_template(brief, sheet, assessment_type="practice_exam").errors


def test_the_cli_routes_a_theory_exam_by_the_files_given(tmp_path, capsys):
    for path in (THEORY, THEORY_RUBRIC, TEMPLATE):
        shutil.copy(path, tmp_path / path.name)
    argv = [
        "--no-venv",
        "assessment",
        "verify",
        "--type",
        "theory_exam",
        "--brief",
        str(tmp_path / THEORY.name),
        "--rubric",
        str(tmp_path / THEORY_RUBRIC.name),
        "--answer-template",
        str(tmp_path / TEMPLATE.name),
        "--max-pages",
        "10",
    ]
    assert main(argv) == 0
    assert "PASS" in capsys.readouterr().out


def test_the_cli_refuses_both_forms_at_once(tmp_path):
    argv = [
        "--no-venv",
        "assessment",
        "verify",
        "--type",
        "quiz",
        "--master",
        str(tmp_path / "q.csv"),
        "--brief",
        str(THEORY),
    ]
    with pytest.raises(UsageError):
        main(argv)
