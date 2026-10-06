"""The workbook editor.

The whole design rests on one claim: parts we do not write come out unchanged.
Everything else — inline strings, style preservation, the calc chain, the sheet
rename — exists because the real vendor form does something that punishes the
naive approach. These are the tests that make the claim checkable, so they run
against a synthetic workbook carrying the same awkward features rather than
against a proprietary file CI cannot have.
"""

from __future__ import annotations

import zipfile

import pytest

from get_fsa_training_done.errors import FsaTrainerSkillsError, UsageError
from get_fsa_training_done.skills.program.core.xlsx import probe as probe_mod
from get_fsa_training_done.skills.program.core.xlsx import refs
from get_fsa_training_done.skills.program.core.xlsx.package import XlsxPackage

SYLLABUS = "<Topic Code>_Syllabus"


def parts(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def order(path):
    with zipfile.ZipFile(path) as archive:
        return archive.namelist()


# --- References -----------------------------------------------------------


@pytest.mark.parametrize(
    ("letters", "index"), [("A", 1), ("Z", 26), ("AA", 27), ("CR", 96), ("XFD", 16384)]
)
def test_column_letters_round_trip(letters, index):
    assert refs.column_index(letters) == index
    assert refs.column_letter(index) == letters


def test_a_range_expands_row_by_row():
    assert refs.expand("A1:B2") == ["A1", "B1", "A2", "B2"]


def test_bounds_is_the_covering_rectangle():
    assert refs.bounds(["C3", "A1", "B10"]) == "A1:C10"


# --- Part preservation ----------------------------------------------------


def test_a_save_with_no_edits_preserves_every_part(synthetic_xlsx, tmp_path):
    out = tmp_path / "out.xlsx"
    XlsxPackage(synthetic_xlsx).save(out)

    assert parts(out) == parts(synthetic_xlsx)
    assert order(out) == order(synthetic_xlsx)


def test_editing_one_sheet_leaves_the_others_byte_identical(synthetic_xlsx, tmp_path):
    """The reason this exists: a library round-trip drops parts it does not
    model — on the real form, the sensitivity label, the custom properties and
    all four printer-settings blobs."""
    package = XlsxPackage(synthetic_xlsx)
    sheet = package.sheet(SYLLABUS)
    sheet.set_text("A1", "Database Foundations")
    package.write_sheet(SYLLABUS, sheet)
    out = tmp_path / "out.xlsx"
    package.save(out)

    before, after = parts(synthetic_xlsx), parts(out)
    changed = {name for name in before if before[name] != after.get(name)}
    assert changed == {"xl/worksheets/sheet2.xml"}
    assert after["xl/printerSettings/printerSettings1.bin"] == b"\x00opaque-binary-part\x00"
    assert after["xl/sharedStrings.xml"] == before["xl/sharedStrings.xml"]


def test_content_types_stays_the_first_entry(synthetic_xlsx, tmp_path):
    package = XlsxPackage(synthetic_xlsx)
    package.drop_calc_chain()
    out = tmp_path / "out.xlsx"
    package.save(out)

    assert order(out)[0] == "[Content_Types].xml"


def test_a_non_xlsx_template_is_refused_with_the_reason(tmp_path):
    """The curriculum form ships as .xls, which is not an Open XML package."""
    legacy = tmp_path / "Template.xls"
    legacy.write_bytes(b"\xd0\xcf\x11\xe0 OLE compound document")
    with pytest.raises(UsageError, match="not a .xlsx"):
        XlsxPackage(legacy)


# --- Cells ----------------------------------------------------------------


def test_a_string_is_written_inline_and_shared_strings_is_untouched(synthetic_xlsx, tmp_path):
    package = XlsxPackage(synthetic_xlsx)
    sheet = package.sheet(SYLLABUS)
    sheet.set_text("A1", "New title")
    package.write_sheet(SYLLABUS, sheet)
    out = tmp_path / "out.xlsx"
    package.save(out)

    body = parts(out)["xl/worksheets/sheet2.xml"].decode()
    assert 't="inlineStr"' in body
    assert "New title" in body
    assert parts(out)["xl/sharedStrings.xml"] == parts(synthetic_xlsx)["xl/sharedStrings.xml"]


def test_writing_over_a_shared_string_cell_drops_its_index(synthetic_xlsx):
    package = XlsxPackage(synthetic_xlsx)
    sheet = package.sheet(SYLLABUS)
    assert sheet.value_of("A1") == "0"  # the shared-string index

    sheet.set_text("A1", "Replaced")

    element = sheet.cell("A1")
    assert element.get("t") == "inlineStr"
    assert element.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v") is None


def test_every_edit_keeps_the_style_the_template_supplies(synthetic_xlsx):
    """This writer never creates a style; it populates a formatted template."""
    sheet = XlsxPackage(synthetic_xlsx).sheet(SYLLABUS)
    for ref, setter in (
        ("A1", lambda: sheet.set_text("A1", "x")),
        ("A2", lambda: sheet.set_number("A2", 42)),
        ("B3", lambda: sheet.set_formula("B3", "SUM(A2:A2)")),
    ):
        before = sheet.style_of(ref)
        setter()
        assert sheet.style_of(ref) == before, ref


def test_a_number_is_written_as_a_number(synthetic_xlsx):
    """The template's summary is a SUMIF over the duration column, and it
    silently returns 0 when the durations are text."""
    sheet = XlsxPackage(synthetic_xlsx).sheet(SYLLABUS)
    sheet.set_number("A2", 240)

    element = sheet.cell("A2")
    assert element.get("t") is None
    assert sheet.value_of("A2") == "240"


def test_writing_a_literal_over_a_formula_removes_the_formula(synthetic_xlsx):
    """B3 is `<f>SUM(A2:A2)</f><v>1</v>` — leaving either behind shows a stale
    number rather than the value just written."""
    sheet = XlsxPackage(synthetic_xlsx).sheet(SYLLABUS)
    sheet.set_number("B3", 99)

    element = sheet.cell("B3")
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    assert element.find(f"{ns}f") is None
    assert sheet.value_of("B3") == "99"


def test_writing_a_formula_removes_the_cached_value(synthetic_xlsx):
    sheet = XlsxPackage(synthetic_xlsx).sheet(SYLLABUS)
    sheet.set_formula("B3", "SUM(A2:A3)")

    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    element = sheet.cell("B3")
    assert element.find(f"{ns}v") is None
    assert element.find(f"{ns}f").text == "SUM(A2:A3)"


def test_clearing_keeps_the_cell_and_its_formatting(synthetic_xlsx):
    sheet = XlsxPackage(synthetic_xlsx).sheet(SYLLABUS)
    sheet.clear("A2")

    assert sheet.value_of("A2") is None
    assert sheet.style_of("A2") == "11"


def test_new_rows_and_cells_are_inserted_in_order(synthetic_xlsx):
    sheet = XlsxPackage(synthetic_xlsx).sheet(SYLLABUS)
    sheet.set_text("B4", "later")
    sheet.set_text("A4", "earlier")
    sheet.set_text("A2", "existing row")

    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rows = [int(r.get("r")) for r in sheet.sheet_data.findall(f"{ns}row")]
    assert rows == sorted(rows)
    row4 = next(r for r in sheet.sheet_data.findall(f"{ns}row") if r.get("r") == "4")
    assert [c.get("r") for c in row4.findall(f"{ns}c")] == ["A4", "B4"]


def test_the_dimension_is_recomputed(synthetic_xlsx, tmp_path):
    """Excel treats it as a hint; LibreOffice trusts it."""
    package = XlsxPackage(synthetic_xlsx)
    sheet = package.sheet(SYLLABUS)
    sheet.set_text("F9", "far corner")
    package.write_sheet(SYLLABUS, sheet)

    assert "F9" in parts_of_sheet(package)


def parts_of_sheet(package):
    return package.parts[package.sheet_part(SYLLABUS)].decode()


def test_merges_are_rewritten_with_the_count_in_step(synthetic_xlsx):
    sheet = XlsxPackage(synthetic_xlsx).sheet(SYLLABUS)
    assert sheet.merges() == ["A1:B1"]

    sheet.set_merges(["A1:B1", "A5:C5"])

    assert sheet.merges() == ["A1:B1", "A5:C5"]
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    assert sheet.root.find(f"{ns}mergeCells").get("count") == "2"


# --- Workbook-level surgery ----------------------------------------------


def test_the_calc_chain_is_dropped_with_its_relationship_and_override(synthetic_xlsx, tmp_path):
    """A chain naming cells whose formulas changed makes Excel report the file
    as unreadable."""
    package = XlsxPackage(synthetic_xlsx)
    package.drop_calc_chain()
    out = tmp_path / "out.xlsx"
    package.save(out)

    written = parts(out)
    assert "xl/calcChain.xml" not in written
    assert b"calcChain" not in written["[Content_Types].xml"]
    assert b"calcChain" not in written["xl/_rels/workbook.xml.rels"]


def test_full_recalc_is_requested(synthetic_xlsx, tmp_path):
    package = XlsxPackage(synthetic_xlsx)
    package.force_full_recalc()
    out = tmp_path / "out.xlsx"
    package.save(out)

    assert b'fullCalcOnLoad="1"' in parts(out)["xl/workbook.xml"]


def test_renaming_a_sheet_updates_the_defined_name_that_quotes_it(synthetic_xlsx, tmp_path):
    """The real form's `_xlnm._FilterDatabase` quotes the schedule sheet by
    name. Missing it yields `#REF!` in Excel."""
    package = XlsxPackage(synthetic_xlsx)
    package.rename_sheet(SYLLABUS, "AA_FR_TT_DBF_Syllabus")
    out = tmp_path / "out.xlsx"
    package.save(out)

    workbook = parts(out)["xl/workbook.xml"].decode()
    assert "AA_FR_TT_DBF_Syllabus" in workbook
    assert "&lt;Topic Code&gt;_Syllabus" not in workbook
    assert "'AA_FR_TT_DBF_Syllabus'!$A$1:$C$2" in workbook


def test_a_sheet_name_excel_would_reject_is_refused(synthetic_xlsx):
    package = XlsxPackage(synthetic_xlsx)
    with pytest.raises(UsageError, match="the limit is 31"):
        package.rename_sheet(SYLLABUS, "A" * 32)
    with pytest.raises(UsageError, match="forbids"):
        package.rename_sheet(SYLLABUS, "bad/name")
    with pytest.raises(UsageError, match="already has a sheet"):
        package.rename_sheet(SYLLABUS, "Cover")


def test_the_longest_real_sheet_name_is_accepted(synthetic_xlsx):
    """`HN_FR_JSKS_SBAD_ScheduleDetail` is 30 characters — one under the limit,
    which is why the check earns its place rather than being theoretical."""
    name = "HN_FR_JSKS_SBAD_ScheduleDetail"
    assert len(name) == 30
    XlsxPackage(synthetic_xlsx).rename_sheet(SYLLABUS, name)


def test_dropping_a_sheet_removes_its_part_and_renumbers_defined_names(synthetic_xlsx, tmp_path):
    """`localSheetId` is a position in the sheet list, so removing one shifts
    every later index."""
    package = XlsxPackage(synthetic_xlsx)
    package.drop_sheet("Cover")
    out = tmp_path / "out.xlsx"
    package.save(out)

    written = parts(out)
    assert "xl/worksheets/sheet1.xml" not in written
    workbook = written["xl/workbook.xml"].decode()
    assert "Cover" not in workbook
    # The syllabus was index 1 and is now index 0; the name pinned to the
    # removed sheet is gone rather than pointing at a survivor.
    assert 'localSheetId="0"' in workbook
    assert "Stale" not in workbook


def test_an_unknown_sheet_name_says_what_is_there(synthetic_xlsx):
    with pytest.raises(UsageError, match="no sheet named"):
        XlsxPackage(synthetic_xlsx).sheet_part("Nope")


# --- Probe ----------------------------------------------------------------


def test_the_probe_accepts_a_template_that_matches(synthetic_xlsx):
    package = XlsxPackage(synthetic_xlsx)
    probe_mod.require(
        package,
        ["Cover", SYLLABUS],
        [probe_mod.Expect(SYLLABUS, "A2", "1")],
    )


def test_the_probe_names_the_cell_that_disagreed(synthetic_xlsx):
    """The point is the diagnosis, not the refusal: a writer addressing a moved
    anchor does not fail, it writes the right value into the wrong cell."""
    package = XlsxPackage(synthetic_xlsx)
    with pytest.raises(FsaTrainerSkillsError) as raised:
        probe_mod.require(package, [SYLLABUS], [probe_mod.Expect(SYLLABUS, "A2", "99")])
    assert "A2" in raised.value.hint
    assert "'99'" in raised.value.hint


def test_the_probe_reports_a_missing_sheet(synthetic_xlsx):
    package = XlsxPackage(synthetic_xlsx)
    with pytest.raises(FsaTrainerSkillsError) as raised:
        probe_mod.require(package, ["Nope"], [])
    assert "missing sheet" in raised.value.hint


def test_an_expectation_may_allow_a_revised_wording(synthetic_xlsx):
    package = XlsxPackage(synthetic_xlsx)
    probe_mod.require(
        package,
        [SYLLABUS],
        [probe_mod.Expect(SYLLABUS, "A2", "Duration (weeks)", alternatives=("1",))],
    )


def test_a_template_carrying_stale_error_names_still_probes(synthetic_xlsx):
    """Two of the real form's three defined names are already `#REF!`, so the
    error scan looks at cell values, not defined names."""
    package = XlsxPackage(synthetic_xlsx)
    assert b"#REF!" in package.parts["xl/workbook.xml"]
    assert probe_mod.error_cells(package, SYLLABUS) == []


# --- The real vendor form -------------------------------------------------


def real_template():
    """The proprietary FPT form, when a developer points at a local copy.

    It cannot be committed, so CI exercises the synthetic workbook above. This
    runs the same claim against the real thing when `FSA_PROGRAM_TEMPLATE` is
    set, which is where a template revision would first show up.
    """
    import os

    raw = os.environ.get("FSA_PROGRAM_TEMPLATE")
    return __import__("pathlib").Path(raw) if raw else None


@pytest.mark.skipif(real_template() is None, reason="FSA_PROGRAM_TEMPLATE not set")
def test_the_real_template_survives_a_full_edit(tmp_path):
    template = real_template()
    package = XlsxPackage(template)
    syllabus_sheet = "<Topic Code>_Syllabus"
    schedule_sheet = "<Topics Code>_ScheduleDetail"

    sheet = package.sheet(syllabus_sheet)
    sheet.set_text("C3", "Database Foundations")
    package.write_sheet(syllabus_sheet, sheet)
    package.rename_sheet(schedule_sheet, "AA_FR_TT_DBF_ScheduleDetail")
    package.rename_sheet(syllabus_sheet, "AA_FR_TT_DBF_Syllabus")
    package.drop_sheet("DV-IDENTITY-0")
    package.force_full_recalc()
    package.drop_calc_chain()
    out = tmp_path / "out.xlsx"
    package.save(out)

    before, after = parts(template), parts(out)
    # Only the calc chain and the dropped sheet's two parts may disappear.
    assert set(before) - set(after) <= {
        "xl/calcChain.xml",
        "xl/worksheets/sheet5.xml",
        "xl/worksheets/_rels/sheet5.xml.rels",
    }
    assert set(after) - set(before) == set()

    rewritten = {"xl/workbook.xml", "[Content_Types].xml", "xl/_rels/workbook.xml.rels"}
    rewritten |= {n for n in after if n.startswith("xl/worksheets/sheet")}
    untouched = [n for n in set(before) & set(after) if n not in rewritten]
    assert [n for n in untouched if before[n] != after[n]] == []

    # The label, the custom properties and the print setup are exactly what
    # a library round-trip loses.
    for survivor in (
        "docMetadata/LabelInfo.xml",
        "xl/customProperty1.bin",
        "xl/printerSettings/printerSettings1.bin",
        "xl/media/image1.png",
    ):
        if survivor in before:
            assert after[survivor] == before[survivor], survivor

    workbook = after["xl/workbook.xml"].decode()
    assert "&lt;Topics Code&gt;_ScheduleDetail" not in workbook
    assert "'AA_FR_TT_DBF_ScheduleDetail'!" in workbook
