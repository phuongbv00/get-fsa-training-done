"""The hand-rolled XLSX reader and the quiz scoring rule."""

from __future__ import annotations

import zipfile

import pytest

from fsa_trainer_skills.errors import UsageError
from fsa_trainer_skills.skills.assess.core.grading import quiz_scores
from fsa_trainer_skills.skills.assess.core.grading import roster as roster_mod

NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
RNS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def write_xlsx(path, rows):
    """A minimal two-sheet workbook: sheet 1 is empty, sheet 2 holds `rows`.

    Text cells go through the shared-string table, numbers stay inline, so both
    cell kinds the reader handles are exercised.
    """
    shared: list[str] = []

    def cell(ref, value):
        if isinstance(value, str):
            shared.append(value)
            return f'<c r="{ref}" t="s"><v>{len(shared) - 1}</v></c>'
        return f'<c r="{ref}"><v>{value}</v></c>'

    body = "".join(
        f'<row r="{r}">'
        + "".join(cell(f"{chr(65 + c)}{r}", value) for c, value in enumerate(row))
        + "</row>"
        for r, row in enumerate(rows, start=1)
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            f'<workbook {NS} {RNS}><sheets><sheet name="Q" sheetId="1" r:id="rId1"/>'
            '<sheet name="Players" sheetId="2" r:id="rId2"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>',
        )
        archive.writestr("xl/worksheets/sheet1.xml", f"<worksheet {NS}><sheetData/></worksheet>")
        archive.writestr(
            "xl/worksheets/sheet2.xml", f"<worksheet {NS}><sheetData>{body}</sheetData></worksheet>"
        )
        archive.writestr(
            "xl/sharedStrings.xml",
            f"<sst {NS}>" + "".join(f"<si><t>{s}</t></si>" for s in shared) + "</sst>",
        )


@pytest.fixture
def report(tmp_path):
    path = tmp_path / "report.xlsx"
    write_xlsx(
        path,
        [
            ["Nickname", "Qs Answered", "Correct", "Incorrect", "Unattempted"],
            ["phuongbv3", 10, 7, 3, 0],
            ["LinhTT127", 8, 8, 0, 2],
            ["HieuLX14", 10, 10, 0, 0],
            ["stranger", 10, 5, 5, 0],
        ],
    )
    return path


def test_reads_the_second_sheet_through_shared_strings(report):
    rows = quiz_scores.read_sheet(report, 2)
    assert rows[0] == ["Nickname", "Qs Answered", "Correct", "Incorrect", "Unattempted"]
    assert rows[1] == ["phuongbv3", "10", "7", "3", "0"]


def test_sheet_index_out_of_range_is_a_usage_error(report):
    with pytest.raises(UsageError, match="sheet"):
        quiz_scores.read_sheet(report, 3)


def test_scores_round_up_and_count_unattempted_against_the_trainee(report, roster_csv):
    result = quiz_scores.score(quiz_scores.read_sheet(report, 2), roster_mod.load(roster_csv))
    scores = dict(result.rows[1:])
    # 7/10 exactly; 8/(8+2) — the two unattempted questions count as asked.
    assert scores == {"PhuongBV3": "7.0", "LinhTT127": "8.0"}
    assert result.dropped == ["HieuLX14"]
    assert result.unmatched == ["stranger"]


def test_one_third_rounds_up_to_the_next_tenth():
    rows = [["Nickname", "Qs Answered", "Correct", "Incorrect", "Unattempted"], ["a", 3, 1, 2, 0]]
    assert quiz_scores.score(rows, None).rows[1] == ["a", "3.4"]
