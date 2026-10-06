"""The hand-rolled XLSX reader and the quiz scoring rule."""

from __future__ import annotations

import zipfile

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.assessment.core.grading import quiz_scores
from get_fsa_training_done.features.assessment.core.grading import roster as roster_mod

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


# --- Blooket leaderboard pastes ----------------------------------------------

ICON = '<svg aria-hidden="true" class="svg-inline--fa"><path d="M0 0"></path></svg>'


def player(name, correct=None, incorrect=None, *, card=False):
    """One player as Blooket renders it: table row or card, icon in each label."""
    bar = '<div class="ColumnTemplates_accuracyBarContainer__i9IxW">'
    if correct is not None:
        bar += (
            '<div class="ColumnTemplates_correctAnswersBar__AvV1U" style="width: 90%;">'
            f'<div class="ColumnTemplates_barText__KwKAE">{ICON}{correct}</div></div>'
        )
    if incorrect is not None:
        bar += f'<div class="ColumnTemplates_barText__KwKAE">{ICON}{incorrect}</div>'
    bar += "</div>"
    name_cell = f'<span class="ColumnTemplates_student__eQ3gW">{name}</span>'
    metric = '<div class="ColumnTemplates_columnCell__krvNs">1,234,567</div>'
    if card:
        return f'<div class="Table_card___DvOG">{name_cell}{metric}{bar}</div>'
    cells = f"<td>1st</td><td>{name_cell}</td><td>{bar}</td><td>{metric}</td>"
    return f'<tr class="Table_row__ypKHf">{cells}</tr>'


def leaderboard(tmp_path, name, players):
    path = tmp_path / name
    path.write_text(f"<div>Leaderboard<table>{''.join(players)}</table></div>", encoding="utf-8")
    return path


def read_csv(path):
    import csv

    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.reader(handle))


def test_leaderboard_rows_follow_the_bar_labels(tmp_path):
    path = leaderboard(
        tmp_path,
        "q.html",
        [
            player("PhuongBV3", 36, 1),
            player("LinhTT127", 46, 8, card=True),
            player("perfect", 40),
            player("lost", None, 5),
        ],
    )
    rows = quiz_scores.read_leaderboard(path, 40)
    assert rows[1:] == [
        ["PhuongBV3", "37", "36", "1", "3"],
        ["LinhTT127", "54", "46", "8", "0"],
        ["perfect", "40", "40", "0", "0"],
        ["lost", "5", "0", "5", "35"],
    ]


def test_scores_use_the_quiz_size_or_what_was_answered_whichever_is_larger(tmp_path):
    """The numbers the instructor confirmed by hand for a 40-question quiz."""
    path = leaderboard(tmp_path, "q.html", [player("PhuongBV3", 36, 1), player("LinhTT127", 46, 8)])
    result = quiz_scores.score(quiz_scores.read_leaderboard(path, 40), None)
    assert result.rows[1:] == [["PhuongBV3", "9.0"], ["LinhTT127", "8.6"]]


def test_a_trainee_who_played_twice_keeps_the_best_attempt(tmp_path, roster_csv):
    live = leaderboard(tmp_path, "live.html", [player("phuongbv3", 20, 2)])
    home = leaderboard(tmp_path, "home.html", [player("PhuongBV3", 30, 1)])
    out = tmp_path / "q.csv"
    argv = ["--no-venv", "assessment", "grade", "quiz", "--html", str(live), "--html", str(home)]
    argv += ["--questions", "40", "--roster", str(roster_csv), "--out", str(out)]
    assert main(argv) == 0
    assert read_csv(out)[1:] == [["PhuongBV3", "7.5"]]


def test_an_alias_maps_a_loose_nickname(tmp_path, roster_csv):
    path = leaderboard(tmp_path, "q.html", [player("Linh T", 40, 0)])
    rows = quiz_scores.read_leaderboard(path, 40)
    result = quiz_scores.score(rows, roster_mod.load(roster_csv), {"linh t": "LinhTT127"})
    assert result.rows[1:] == [["LinhTT127", "10.0"]]
    assert result.unmatched == []


def test_names_are_read_as_text_not_markup(tmp_path):
    path = leaderboard(tmp_path, "q.html", [player("O&#39;Neil &amp; co", 10, 0)])
    assert quiz_scores.read_leaderboard(path, 10)[1][0] == "O'Neil & co"


def test_html_without_questions_is_refused(tmp_path):
    path = leaderboard(tmp_path, "q.html", [player("PhuongBV3", 1, 1)])
    argv = ["--no-venv", "assessment", "grade", "quiz", "--html", str(path)]
    with pytest.raises(UsageError):
        main(argv + ["--out", str(tmp_path / "q.csv")])


def test_a_page_with_no_players_is_refused(tmp_path):
    path = tmp_path / "q.html"
    path.write_text("<html>not a leaderboard</html>", encoding="utf-8")
    with pytest.raises(UsageError):
        quiz_scores.read_leaderboard(path, 40)
