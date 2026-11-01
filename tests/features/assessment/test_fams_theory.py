"""Quiz and theory-exam marks in FAMS's theory mark template."""

from __future__ import annotations

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.assessment.core.grading import fams_theory, quiz_scores
from get_fsa_training_done.features.assessment.core.grading import roster as roster_mod


def grade(*argv):
    return main(["--no-venv", "assessment", "grade", *map(str, argv)])


@pytest.fixture
def scores(tmp_path):
    path = tmp_path / "jcf_quiz_scores.csv"
    path.write_text(
        "No,ID,Name,JCF 01,JCF 02\n"
        "1,PhuongBV3,Bui Van Phuong,7.5,\n"
        "2,LinhTT127,Tran Thi Linh,8.6,8.0\n",
        encoding="utf-8-sig",
    )
    return path


@pytest.fixture
def theory_grades(tmp_path):
    path = tmp_path / "jcf_t_exam_01_grades.csv"
    path.write_text(
        "Std ID,Name,Comment,T1 (50%),T2 (50%),Total\nPhuongBV3,Bui Van Phuong,Tốt.,8,9,8.5\n",
        encoding="utf-8-sig",
    )
    return path


@pytest.fixture
def cpl_roster(tmp_path):
    path = tmp_path / "std_list.csv"
    path.write_text(
        "No,ID,Name,Status,Account\n"
        "1,PhuongBV3,Bui Van Phuong,active,\n"
        "2,LinhTT127,Tran Thi Linh,active,linh.tran@example.com\n"
        "3,AnNV9,Nguyen Van An,dropped,\n",
        encoding="utf-8-sig",
    )
    return path


def test_without_a_template_the_class_is_the_active_roster(scores, cpl_roster, tmp_path):
    out = tmp_path / "fams.xlsx"
    assert (
        grade(
            "export",
            "fams",
            "theory",
            "--quiz-scores",
            scores,
            "--roster",
            cpl_roster,
            "--topic-code",
            "FR_JSKS_JCF",
            "--out",
            out,
        )
        == 0
    )
    assert quiz_scores.read_sheet(out, 1) == [
        fams_theory.HEADERS,
        ["PhuongBV3", "Bui Van Phuong", "FR_JSKS_JCF", "Quiz_1", "7.5", "7.5", "10"],
        # The roster's Account wins: a CPL trainee is known by personal email.
        ["linh.tran@example.com", "Tran Thi Linh", "FR_JSKS_JCF", "Quiz_1", "8.6", "8.6", "10"],
        # FAMS refuses a blank mark, so a missed quiz is 0.
        ["PhuongBV3", "Bui Van Phuong", "FR_JSKS_JCF", "Quiz_2", "0", "0", "10"],
        ["linh.tran@example.com", "Tran Thi Linh", "FR_JSKS_JCF", "Quiz_2", "8", "8", "10"],
    ]


def test_without_a_template_the_topic_code_is_required(scores, cpl_roster):
    with pytest.raises(UsageError, match="topic-code"):
        fams_theory.build(
            fams_theory.read_quiz_scores(scores),
            names=["Quiz_1", "Quiz_2"],
            roster=roster_mod.load(cpl_roster),
            topic_code=None,
        )


def test_the_template_decides_who_is_in_the_class(scores, cpl_roster):
    template = [
        [*fams_theory.HEADERS, "Topic Extra Score"],
        ["phuong@example.com", "Bùi Văn Phương", "FR_JSKS_JCF", "Quiz_1"],
        ["anh@example.com", "Pham Quynh Anh", "FR_JSKS_JCF", "Quiz_1"],
        # A template stacks a row per test: the class is still each trainee once.
        ["phuong@example.com", "Bùi Văn Phương", "FR_JSKS_JCF", "Quiz_2"],
    ]
    source = fams_theory.read_quiz_scores(scores)
    source.entries[0] = fams_theory.Entry("PhuongBV3", "Bùi Văn Phương", ("7.5", ""))
    sheet, report = fams_theory.build(
        source,
        names=fams_theory.test_names(source, ["JCF 02=Quiz_B"]),
        roster=roster_mod.load(cpl_roster),
        topic_code=None,
        template=template,
    )
    assert sheet.headers == template[0]
    assert [row[:7] for row in sheet.rows] == [
        # Matched by name; the template's email gives way to the FPT account.
        ["PhuongBV3", "Bùi Văn Phương", "FR_JSKS_JCF", "Quiz_1", 7.5, 7.5, 10.0],
        ["anh@example.com", "Pham Quynh Anh", "FR_JSKS_JCF", "Quiz_1", 0.0, 0.0, 10.0],
        ["PhuongBV3", "Bùi Văn Phương", "FR_JSKS_JCF", "Quiz_B", 0.0, 0.0, 10.0],
        ["anh@example.com", "Pham Quynh Anh", "FR_JSKS_JCF", "Quiz_B", 0.0, 0.0, 10.0],
    ]
    assert report.left_out == ["LinhTT127"]
    assert report.zeroed == ["Pham Quynh Anh"]
    assert report.unmatched == ["Pham Quynh Anh"]
    assert report.missed == [("Quiz_B", "PhuongBV3")]


def test_an_assessment_label_must_name_a_quiz(scores):
    with pytest.raises(UsageError, match="--assessment"):
        fams_theory.test_names(fams_theory.read_quiz_scores(scores), ["JCF 09=Quiz_9"])


def test_a_theory_exam_grade_csv_is_one_test_named_by_its_code(theory_grades, cpl_roster, tmp_path):
    out = tmp_path / "theory.xlsx"
    assert (
        grade(
            "export",
            "fams",
            "theory",
            "--grades",
            theory_grades,
            "--roster",
            cpl_roster,
            "--topic-code",
            "FR_JSKS_JCF",
            "--assessment",
            "Final Theory Exam_1",
            "--out",
            out,
        )
        == 0
    )
    assert [row[3:5] for row in quiz_scores.read_sheet(out, 1)[1:]] == [
        ["Final Theory Exam_1", "8.5"],
        # Not graded: written as 0, never blank.
        ["Final Theory Exam_1", "0"],
    ]


def test_a_theory_exam_takes_its_code_from_the_template_or_must_be_told(theory_grades):
    source = fams_theory.read_grades(theory_grades)
    template = [
        fams_theory.HEADERS,
        ["PhuongBV3", "Bui Van Phuong", "FR_JSKS_JCF", "Final Theory Exam_1"],
    ]
    assert fams_theory.test_names(source, [], template) == ["Final Theory Exam_1"]
    with pytest.raises(UsageError, match="pass --assessment"):
        fams_theory.test_names(source, [])


def test_a_retake_lists_only_its_takers(theory_grades, cpl_roster, tmp_path):
    template = tmp_path / "class.xlsx"
    rows = [
        list(fams_theory.HEADERS),
        ["a@gmail.com", "Bui Van Phuong", "FR_JSKS_JCF", "Quiz_1", 7.0, 7.0, 10.0],
        ["b@gmail.com", "Tran Thi Linh", "FR_JSKS_JCF", "Quiz_1", 8.0, 8.0, 10.0],
    ]
    fams_theory.write(fams_theory.Sheet(headers=rows[0], rows=rows[1:]), template)
    out = tmp_path / "retake.xlsx"
    report = fams_theory.export_theory(
        fams_theory.read_grades(theory_grades),
        out,
        roster=roster_mod.load(cpl_roster),
        template=template,
        topic_code=None,
        assessments=["Final Theory Exam_2"],
        graded_only=True,
    )
    assert report.zeroed == []
    assert report.notes == ["no marks, left off (graded only): LinhTT127"]
    assert quiz_scores.read_sheet(out, 1)[1:] == [
        ["PhuongBV3", "Bui Van Phuong", "FR_JSKS_JCF", "Final Theory Exam_2", "8.5", "8.5", "10"]
    ]
