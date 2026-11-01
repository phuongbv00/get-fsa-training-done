"""Assignment and practice-exam marks in FAMS's practice mark template."""

from __future__ import annotations

import zipfile

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.assessment.core.grading import fams_practice
from get_fsa_training_done.features.assessment.core.grading import roster as roster_mod
from get_fsa_training_done.features.common.xlsx import refs
from get_fsa_training_done.features.common.xlsx.package import XlsxPackage


def grade(*argv):
    return main(["--no-venv", "assessment", "grade", *map(str, argv)])


def roster(tmp_path, *lines):
    path = tmp_path / "std_list.csv"
    path.write_text("\n".join(["No,ID,Name,Status,Account", *lines]) + "\n", encoding="utf-8-sig")
    return path


def grades(tmp_path, header, *lines):
    path = tmp_path / "jcf_assignment_grades.csv"
    path.write_text("\n".join([header, *lines]) + "\n", encoding="utf-8-sig")
    return path


TWO_TASKS = "Std ID,Name,Comment,T1 (40%),T2 (60%),Total"


def cells(path):
    """Every cell's literal text — inline string, cached value — by reference."""
    package = XlsxPackage(path)
    sheet = package.sheet(package.sheet_names()[0])
    return {ref: sheet.value_of(ref) for ref in sheet.refs_present()}, sheet


def formula(sheet, ref):
    node = sheet.cell(ref, create=False).find(
        "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}f"
    )
    return node.text if node is not None else None


def template(tmp_path, trainees, questions=3):
    """A FAMS-shaped form, as `write_form` lays it out, standing in for the
    customer's template, which is never committed."""
    path = tmp_path / "Template_Mark.xlsx"
    tasks = [fams_practice.Task(f"T{k + 1}", 10) for k in range(questions)]
    fams_practice.write_form(
        path,
        roster_mod.load(roster(tmp_path / "tpl", *trainees)),
        tasks,
        pass_mark=6,
        mark_label="\nPractice",
    )
    # A part the export never writes, which must come through untouched.
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr(
            "xl/comments1.xml", "<comments>Required. Không được thay đổi vị trí.</comments>"
        )
    return path


@pytest.fixture
def class_roster(tmp_path):
    (tmp_path / "tpl").mkdir()
    return roster(
        tmp_path,
        "1,PhuongBV3,Bùi Văn Phương,active,",
        "2,LinhTT127,Trần Thùy Linh,active,",
        "3,AnNV9,Nguyễn Văn An,active,an.cpl@gmail.com",
        "4,DropDV1,Đỗ Văn Drop,dropped,",
    )


def test_roster_mode_writes_every_active_trainee_with_cached_marks(tmp_path, class_roster):
    csv_path = grades(
        tmp_path,
        TWO_TASKS,
        'PhuongBV3,Bùi Văn Phương,"T1: tốt. | T2: ổn.",9,8,8.4',
        "AnNV9,Nguyễn Văn An,T1: thiếu test.,5,7,6.2",
    )
    out = tmp_path / "FR_JSKS_JCF_Assignment_Mark.xlsx"
    assert (
        grade(
            "export",
            "fams",
            "practice",
            "--grades",
            csv_path,
            "--roster",
            class_roster,
            "--out",
            out,
            "--topic-code",
            "FR_JSKS_JCF",
            "--assessment",
            "Assignment_1",
            "--marker",
            "PhuongBV3",
            "--date",
            "31/10/2026",
            "--missing-comment",
            "Không nộp bài.",
        )
        == 0
    )
    values, sheet = cells(out)
    assert [values["C3"], values["C4"], values["C5"], values["C6"]] == [
        "FR_JSKS_JCF",
        "Assignment_1",
        "PhuongBV3",
        "31/10/2026",
    ]
    assert [values[r] for r in ("F9", "G9", "H9")] == ["Q1", "Q2", "Bonus"]
    assert [values[r] for r in ("F11", "G11", "H11")] == ["40", "60", "0"]
    # Active trainees only, in roster order; the CPL trainee by the roster's account.
    assert [values[f"B{r}"] for r in (13, 14, 15)] == ["PhuongBV3", "LinhTT127", "an.cpl@gmail.com"]
    assert "B16" not in values or not values["B16"]
    assert formula(sheet, "D13") == "SUMPRODUCT($F$11:$H$11,F13:H13)/SUM($F$11:$H$11)"
    assert float(values["D13"]) == pytest.approx(8.4)
    assert float(values["D15"]) == pytest.approx(6.2)
    # No grade row: zeros and the comment, never a blank mark.
    assert [values["F14"], values["G14"], values["D14"], values["E14"]] == [
        "0",
        "0",
        "0.0",
        "Không nộp bài.",
    ]


def test_template_decides_the_class_and_its_questions_are_laid_out_again(tmp_path, class_roster):
    tpl = template(
        tmp_path,
        [
            "1,x,Bùi Văn Phương,active,phuong.personal@gmail.com",
            "2,y,Trần Thùy Linh,active,linh.personal@gmail.com",
            "3,z,Người Lạ,active,stranger@gmail.com",
        ],
        questions=3,
    )
    csv_path = grades(
        tmp_path,
        TWO_TASKS,
        "PhuongBV3,Bùi Văn Phương,Tốt.,10,5,7",
        "AnNV9,Nguyễn Văn An,Ổn.,6,6,6",
    )
    out = tmp_path / "out.xlsx"
    export = fams_practice.export_practice(
        csv_path,
        out,
        roster=roster_mod.load(class_roster),
        template=tpl,
        topic_code="FR_JSKS_JCF",
        assessment="Assignment_1",
        marker="PhuongBV3",
        date="31/10/2026",
        pass_mark=6,
    )
    assert export.notes == ["the template's 3 question column(s) laid out again"]
    assert export.left_out == ["AnNV9"]  # graded, but FAMS does not list them
    assert export.zeroed == ["LinhTT127", "Người Lạ"]
    assert export.unmatched == ["Người Lạ"]
    values, sheet = cells(out)
    # The template's personal email gives way to the FPT account.
    assert values["B13"] == "PhuongBV3"
    assert values["B15"] == "stranger@gmail.com"
    assert [values.get(r) for r in ("F9", "G9", "H9", "I9")] == ["Q1", "Q2", "Bonus", None]
    assert "I9" not in sheet.refs_present()
    assert sorted(sheet.merges()) == sorted(
        [
            "A8:A11",
            "B8:C8",
            "B12:C12",
            "B9:B10",
            "C9:C10",
            "D9:D10",
            "E9:E10",
            "F9:F10",
            "G9:G10",
            "H9:H10",
        ]
    )
    assert values["D9"] == "\nPractice"
    assert float(values["D13"]) == pytest.approx(7.0)
    assert formula(sheet, "D12") == "SUMPRODUCT($F$11:$H$11,F12:H12)/SUM($F$11:$H$11)"
    with zipfile.ZipFile(tpl) as before, zipfile.ZipFile(out) as after:
        assert after.read("xl/comments1.xml") == before.read("xl/comments1.xml")


def test_more_tasks_than_the_template_has_questions(tmp_path, class_roster):
    tpl = template(tmp_path, ["1,x,Bùi Văn Phương,active,"], questions=2)
    header = "Std ID,Name,Comment,T1 (10%),T2 (20%),T3 (30%),T4 (40%),Total"
    csv_path = grades(tmp_path, header, "PhuongBV3,Bùi Văn Phương,Tốt.,10,10,5,5,6.5")
    out = tmp_path / "out.xlsx"
    fams_practice.export_practice(
        csv_path,
        out,
        roster=roster_mod.load(class_roster),
        template=tpl,
        topic_code="FR_JSKS_JCF",
        assessment="Assignment_1",
        marker="PhuongBV3",
        date=None,
        pass_mark=6,
    )
    values, sheet = cells(out)
    assert [values[refs.cell(c, 9)] for c in range(6, 11)] == ["Q1", "Q2", "Q3", "Q4", "Bonus"]
    assert [values[refs.cell(c, 11)] for c in range(6, 11)] == ["10", "20", "30", "40", "0"]
    assert float(values["D13"]) == pytest.approx(6.5)
    assert "J9:J10" in sheet.merges()


def test_template_values_stand_unless_given(tmp_path, class_roster):
    tpl = template(tmp_path, ["1,x,Bùi Văn Phương,active,"], questions=2)
    csv_path = grades(tmp_path, TWO_TASKS, "PhuongBV3,Bùi Văn Phương,Tốt.,10,10,10")
    first = tmp_path / "first.xlsx"
    fams_practice.export_practice(
        csv_path,
        first,
        roster=roster_mod.load(class_roster),
        template=tpl,
        topic_code="FR_JSKS_JCF",
        assessment="Final Practice Test_1",
        marker="PhuongBV3",
        date=None,
        pass_mark=6,
    )
    again = tmp_path / "again.xlsx"
    export = fams_practice.export_practice(
        csv_path,
        again,
        roster=roster_mod.load(class_roster),
        template=first,
        topic_code=None,
        assessment=None,
        marker=None,
        date="01/11/2026",
        pass_mark=6,
    )
    assert export.info["Assessment:"] == "Final Practice Test_1"
    assert export.info["Date:"] == "01/11/2026"


def test_blank_template_fields_must_be_given(tmp_path, class_roster):
    tpl = template(tmp_path, ["1,x,Bùi Văn Phương,active,"], questions=2)
    csv_path = grades(tmp_path, TWO_TASKS, "PhuongBV3,Bùi Văn Phương,Tốt.,10,10,10")
    with pytest.raises(UsageError, match="Assessment is blank"):
        fams_practice.export_practice(
            csv_path,
            tmp_path / "o.xlsx",
            roster=roster_mod.load(class_roster),
            template=tpl,
            topic_code="FR_JSKS_JCF",
            assessment=None,
            marker="PhuongBV3",
            date=None,
            pass_mark=6,
        )


def test_roster_mode_needs_topic_assessment_and_marker(tmp_path, class_roster):
    csv_path = grades(tmp_path, TWO_TASKS, "PhuongBV3,Bùi Văn Phương,Tốt.,10,10,10")
    with pytest.raises(UsageError, match="--assessment, --marker"):
        grade(
            "export",
            "fams",
            "practice",
            "--grades",
            csv_path,
            "--roster",
            class_roster,
            "--out",
            tmp_path / "o.xlsx",
            "--topic-code",
            "FR_JSKS_JCF",
        )


def test_a_task_column_without_its_weight_is_refused(tmp_path, class_roster):
    csv_path = grades(tmp_path, "Std ID,Name,Comment,T1,T2,Total", "PhuongBV3,P,ok,1,2,1.5")
    with pytest.raises(UsageError, match="carries no weight"):
        fams_practice.read_grades(csv_path)


def test_something_else_than_a_marks_table_is_refused(tmp_path, class_roster):
    other = tmp_path / "other.xlsx"
    fams_practice.write_form(
        other,
        roster_mod.load(class_roster),
        [fams_practice.Task("T1", 100)],
        pass_mark=6,
        mark_label="Mark",
    )
    package = XlsxPackage(other)
    sheet = package.sheet("Sheet1")
    sheet.set_text("C11", "Something else")
    package.write_sheet("Sheet1", sheet)
    package.save(other)
    csv_path = grades(tmp_path, "Std ID,Name,Comment,T1 (100%),Total", "PhuongBV3,P,ok,8,8")
    with pytest.raises(UsageError, match="'Passing Score'"):
        fams_practice.export_practice(
            csv_path,
            tmp_path / "o.xlsx",
            roster=roster_mod.load(class_roster),
            template=other,
            topic_code="FR_JSKS_JCF",
            assessment="Assignment_1",
            marker="PhuongBV3",
            date=None,
            pass_mark=6,
        )


def test_a_retake_lists_only_its_takers_with_marks_capped(tmp_path, class_roster):
    tpl = template(
        tmp_path,
        [
            "1,x,Bùi Văn Phương,active,",
            "2,y,Trần Thùy Linh,active,",
            "3,z,Nguyễn Văn An,active,",
        ],
        questions=2,
    )
    csv_path = grades(
        tmp_path,
        TWO_TASKS,
        "LinhTT127,Trần Thùy Linh,Thi lại tốt.,10,9,9.4",
        "AnNV9,Nguyễn Văn An,Thi lại.,5,5,5",
    )
    out = tmp_path / "retake.xlsx"
    report = fams_practice.export_practice(
        csv_path,
        out,
        roster=roster_mod.load(class_roster),
        template=tpl,
        topic_code="FR_JSKS_JCF",
        assessment="Final Practice Exam_2",
        marker="PhuongBV3",
        date=None,
        pass_mark=6,
        cap=6,
        graded_only=True,
    )
    assert report.rows == 2 and report.zeroed == []
    assert "no marks, left off (graded only): PhuongBV3" in report.notes
    assert "capped at 6: LinhTT127" in report.notes
    values, sheet = cells(out)
    # The takers move up into the first rows, numbered again; the rest go.
    assert [values["A13"], values["B13"], values["C13"]] == ["1", "LinhTT127", "Trần Thùy Linh"]
    assert [values["A14"], values["B14"], values["C14"]] == [
        "2",
        "an.cpl@gmail.com",
        "Nguyễn Văn An",
    ]
    assert not any(refs.split(ref)[1] == 15 for ref in sheet.refs_present())
    # Task scores stay as graded; the mark is capped, its value cached.
    assert [values["F13"], values["G13"]] == ["10", "9"]
    assert formula(sheet, "D13") == "MIN(6,SUMPRODUCT($F$11:$H$11,F13:H13)/SUM($F$11:$H$11))"
    assert float(values["D13"]) == pytest.approx(6.0)
    assert float(values["D14"]) == pytest.approx(5.0)
    # The worked example is the form's, never capped.
    assert formula(sheet, "D12") == "SUMPRODUCT($F$11:$H$11,F12:H12)/SUM($F$11:$H$11)"


def test_a_generated_retake_form_lists_only_its_takers(tmp_path, class_roster):
    csv_path = grades(tmp_path, TWO_TASKS, "LinhTT127,Trần Thùy Linh,Ổn.,7,7,7")
    out = tmp_path / "retake.xlsx"
    assert (
        grade(
            "export",
            "fams",
            "practice",
            "--grades",
            csv_path,
            "--roster",
            class_roster,
            "--out",
            out,
            "--topic-code",
            "FR_JSKS_JCF",
            "--assessment",
            "Final Practice Exam_2",
            "--marker",
            "PhuongBV3",
            "--graded-only",
            "--cap",
            "6",
        )
        == 0
    )
    values, _ = cells(out)
    assert values["B13"] == "LinhTT127" and "B14" not in values
    assert float(values["D13"]) == pytest.approx(6.0)
