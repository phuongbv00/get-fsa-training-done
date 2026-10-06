"""Filling the vendor workbook.

The claim these defend is that exporting *edits* the form rather than rebuilding
it: the sheets we populate change and nothing else does. They run against a
synthetic workbook shaped like the real one, because the FPT form is
proprietary and cannot be committed.
"""

from __future__ import annotations

import zipfile

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import GftdError, UsageError
from get_fsa_training_done.features.program.core.xlsx import syllabus_layout as layout
from get_fsa_training_done.features.program.core.xlsx.package import XlsxPackage

DBF = "curriculum/syllabi/AA_FR_TT_DBF_Syllabus.md"
DBF_PLAN = "curriculum/syllabi/AA_FR_TT_DBF_ScheduleDetail.csv"


def parts(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


@pytest.fixture
def exported(mini, vendor_form, tmp_path):
    out = tmp_path / "DBF.xlsx"
    assert (
        main(
            [
                "program",
                "export",
                "syllabus",
                "--template",
                str(vendor_form),
                "--syllabus",
                str(mini / DBF),
                "-o",
                str(out),
            ]
        )
        == 0
    )
    return out


def test_export_writes_a_workbook(exported):
    assert exported.is_file()


def test_only_the_populated_sheets_change(mini, vendor_form, exported):
    """The reason this exporter edits rather than rebuilds: everything the form
    carries beyond its cells has to survive."""
    before, after = parts(vendor_form), parts(exported)
    changed = {name for name in before if before[name] != after.get(name)}
    assert changed <= {
        "xl/workbook.xml",
        "[Content_Types].xml",
        "xl/_rels/workbook.xml.rels",
        "xl/worksheets/sheet2.xml",
        "xl/worksheets/sheet3.xml",
        "xl/worksheets/sheet4.xml",
        "xl/worksheets/sheet5.xml",
        "xl/calcChain.xml",
    }
    assert after["xl/printerSettings/printerSettings1.bin"] == b"\x00opaque-binary-part\x00"
    assert after["xl/sharedStrings.xml"] == before["xl/sharedStrings.xml"]


def test_the_sheets_are_renamed_after_the_topic(exported):
    package = XlsxPackage(exported)
    assert "AA_FR_TT_DBF_Syllabus" in package.sheet_names()
    assert "AA_FR_TT_DBF_ScheduleDetail" in package.sheet_names()
    assert layout.IDENTITY_SHEET not in package.sheet_names()


def test_the_defined_name_follows_the_rename(exported):
    workbook = parts(exported)["xl/workbook.xml"].decode()
    assert "'AA_FR_TT_DBF_ScheduleDetail'!" in workbook
    assert "&lt;Topics Code&gt;" not in workbook


def test_the_session_plan_lands_in_the_band(mini, exported):
    package = XlsxPackage(exported)
    sheet = package.sheet("AA_FR_TT_DBF_ScheduleDetail")
    assert sheet.value_of("B3") == "Relational Modelling"
    assert sheet.value_of("F3") == "Concept/Lecture"
    # Durations must be numbers: the summary block is a SUMIF over them and
    # silently returns zero for text.
    assert sheet.cell("G3").get("t") is None
    assert sheet.value_of("G3") == "60"


def test_the_sample_rows_are_cleared(exported):
    """The template ships sample content in the band."""
    sheet = XlsxPackage(exported).sheet("AA_FR_TT_DBF_ScheduleDetail")
    assert sheet.value_of("D30") is None
    assert "Sample content" not in parts(exported)["xl/worksheets/sheet3.xml"].decode()


def test_the_band_merges_are_rebuilt_around_the_new_rows(exported):
    """The form ships sample merges over the band that would swallow the rows
    written under them, so the band's merges are recomputed from the data.

    The example's first chapter covers sessions 1 and 2 (four rows then three),
    and the second covers session 3 (five rows).
    """
    sheet = XlsxPackage(exported).sheet("AA_FR_TT_DBF_ScheduleDetail")
    merges = sheet.merges()

    band = {m for m in merges if not m.startswith("A2")}
    assert band == {
        "A3:A9",
        "B3:B9",  # chapter 1, sessions 1-2
        "A10:A14",
        "B10:B14",  # chapter 2, session 3
        "C3:C6",
        "C7:C9",
        "C10:C14",  # one span per session
    }
    # The template's own C3:C4 sample span is gone, replaced by the real one.
    assert "C3:C4" not in merges
    # A merge outside the band is left exactly as the form had it.
    assert "A2:B2" in merges


def test_the_time_allocation_stays_a_formula_matched_by_label(exported):
    """The form's summary block lists delivery types in a different order from
    the syllabus table, and leaves two cells as a literal zero. Matching by
    label gets both right."""
    package = XlsxPackage(exported)
    sheet = package.sheet("AA_FR_TT_DBF_Syllabus")
    schedule = package.sheet("AA_FR_TT_DBF_ScheduleDetail")
    by_label = layout.summary_rows_by_label(package, schedule)

    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    for row, label in zip(
        layout.TIME_ROWS,
        [
            "Concept/Lecture",
            "Assignment/Lab",
            "Guides/Review",
            "Seminar/Workshop",
            "Class Meeting",
            "Test/Quiz",
            "Exam",
        ],
        strict=False,
    ):
        formula = sheet.cell(f"D{row}").find(f"{ns}f")
        assert formula is not None, f"D{row} is not a formula"
        assert formula.text.endswith(f"!H{by_label[label]}"), label


def test_the_syllabus_fields_and_scheme_are_written(exported):
    sheet = XlsxPackage(exported).sheet("AA_FR_TT_DBF_Syllabus")
    assert sheet.value_of("C4") == "AA_FR_TT_DBF"
    assert sheet.value_of("C28") == "Quiz"
    assert sheet.value_of("D28") == "2"
    assert sheet.value_of("C32") == "Pass Criteria"
    # Pass Criteria carries no weight, and a zero would be a different claim.
    assert sheet.value_of("E32") is None


def test_authorship_and_the_change_record_are_written(exported):
    sheet = XlsxPackage(exported).sheet("Author and Rec of Changes")
    assert sheet.value_of("C3") == "Demo Author"
    assert sheet.value_of("D10") == "A"


def test_a_full_recalculation_is_requested(exported):
    assert b'fullCalcOnLoad="1"' in parts(exported)["xl/workbook.xml"]


def test_the_calc_chain_is_dropped(exported):
    assert "xl/calcChain.xml" not in parts(exported)


def test_export_refuses_sources_that_do_not_reconcile(mini, vendor_form, tmp_path, edit, capsys):
    """A workbook that looks official and states figures disagreeing with each
    other is worse than no workbook."""
    edit(mini, DBF, "| Exam | 20.83% |", "| Exam | 25.00% |")
    out = tmp_path / "DBF.xlsx"
    code = main(
        [
            "program",
            "export",
            "syllabus",
            "--template",
            str(vendor_form),
            "--syllabus",
            str(mini / DBF),
            "-o",
            str(out),
        ]
    )
    assert code == 1
    assert "PRG-S09" in capsys.readouterr().out
    assert not out.exists()


def test_no_verify_exports_anyway(mini, vendor_form, tmp_path, edit):
    edit(mini, DBF, "| Exam | 20.83% |", "| Exam | 25.00% |")
    out = tmp_path / "DBF.xlsx"
    assert (
        main(
            [
                "program",
                "export",
                "syllabus",
                "--template",
                str(vendor_form),
                "--syllabus",
                str(mini / DBF),
                "-o",
                str(out),
                "--no-verify",
            ]
        )
        == 0
    )
    assert out.is_file()


def test_a_plan_too_long_for_the_band_is_refused(mini, vendor_form, tmp_path, edit):
    """The summary block sits immediately below the band, so overrunning it
    would overwrite the formulas the syllabus reads."""
    plan = mini / DBF_PLAN
    lines = plan.read_text(encoding="utf-8").splitlines()
    header, first = lines[0], lines[1]
    plan.write_text("\n".join([header] + [first] * (layout.MAX_DATA_ROWS + 1)) + "\n", "utf-8")

    with pytest.raises(GftdError, match="band holds"):
        main(
            [
                "program",
                "export",
                "syllabus",
                "--template",
                str(vendor_form),
                "--syllabus",
                str(mini / DBF),
                "-o",
                str(tmp_path / "x.xlsx"),
                "--no-verify",
            ]
        )


def test_export_refuses_to_overwrite_the_template(mini, vendor_form):
    with pytest.raises(UsageError, match="refusing to overwrite the template"):
        main(
            [
                "program",
                "export",
                "syllabus",
                "--template",
                str(vendor_form),
                "--syllabus",
                str(mini / DBF),
                "-o",
                str(vendor_form),
            ]
        )


def test_a_template_with_a_moved_anchor_is_refused(mini, vendor_form, tmp_path):
    """Addressing row 28 is only safe if something confirms the form still puts
    the assessment block there."""
    import shutil

    broken = tmp_path / "Broken.xlsx"
    shutil.copy(vendor_form, broken)
    package = XlsxPackage(broken)
    sheet = package.sheet(layout.SYLLABUS_SHEET)
    sheet.set_number("A28", 99)
    package.write_sheet(layout.SYLLABUS_SHEET, sheet)
    package.save(broken)

    with pytest.raises(GftdError) as raised:
        main(
            [
                "program",
                "export",
                "syllabus",
                "--template",
                str(broken),
                "--syllabus",
                str(mini / DBF),
                "-o",
                str(tmp_path / "x.xlsx"),
            ]
        )
    assert "A28" in raised.value.hint
