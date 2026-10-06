"""Retake merges, Blooket leaderboard pastes, and quizzes side by side."""

from __future__ import annotations

import csv

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.assessment.core.grading import quiz_merge, quiz_scores, retake
from get_fsa_training_done.features.assessment.core.grading import roster as roster_mod

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
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.reader(handle))


# --- Blooket leaderboard ---------------------------------------------------


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


# --- Retake merge ------------------------------------------------------------


def grades(tmp_path, name, rows, tasks=("T1 (50%)", "T2 (50%)")):
    path = tmp_path / name
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Std ID", "Name", "Comment", *tasks, "Total"])
        writer.writerows(rows)
    return path


@pytest.fixture
def attempts(tmp_path):
    first = grades(
        tmp_path,
        "first.csv",
        [
            ["PhuongBV3", "Bui Van Phuong", "T1: first", "4", "4", "4"],
            ["LinhTT127", "Tran Thi Linh", "T1: first", "5", "5", "5"],
            ["AnhPQ54", "Pham Quynh Anh", "T1: first", "3", "3", "3"],
        ],
    )
    second = grades(
        tmp_path,
        "retake.csv",
        [
            ["PhuongBV3", "Bui Van Phuong", "T1: retake", "9", "8", "8.5"],
            ["LinhTT127", "Tran Thi Linh", "T1: retake", "4", "4", "4"],
            ["AnhPQ54", "Pham Quynh Anh", "T1: retake", "9", "9", "9"],
        ],
    )
    return retake.read(first), retake.read(second)


def by_id(merged):
    return {row[0]: row for row in merged.rows}


def test_a_higher_retake_is_kept_and_capped(attempts):
    merged = retake.merge(*attempts)
    row = by_id(merged)["PhuongBV3"]
    # The retake's own task scores and comment, the total capped, and why.
    assert row[2:] == ["T1: retake | Retake: the total is capped at 6.", "9", "8", "6"]
    assert merged.capped == ["PhuongBV3", "AnhPQ54"]


def test_a_lower_retake_leaves_the_first_attempt(attempts):
    row = by_id(retake.merge(*attempts))["LinhTT127"]
    assert row[2:] == ["T1: first", "5", "5", "5"]


def test_a_capped_retake_must_still_beat_the_first_attempt(tmp_path):
    first = retake.read(grades(tmp_path, "f.csv", [["PhuongBV3", "", "first", "7", "6", "6.5"]]))
    second = retake.read(grades(tmp_path, "r.csv", [["PhuongBV3", "", "retake", "9", "9", "9"]]))
    assert by_id(retake.merge(first, second))["PhuongBV3"][-1] == "6.5"


def test_a_voided_retake_keeps_the_first_attempt(attempts):
    merged = retake.merge(*attempts, void=["anhpq54"])
    assert by_id(merged)["AnhPQ54"][2:] == ["T1: first", "3", "3", "3"]
    assert merged.voided == ["AnhPQ54"]


def test_a_voided_retake_with_no_first_attempt_leaves_an_empty_row(tmp_path):
    first = retake.read(grades(tmp_path, "f.csv", [["PhuongBV3", "", "", "4", "4", "4"]]))
    second = retake.read(
        grades(
            tmp_path,
            "r.csv",
            [
                ["PhuongBV3", "", "", "9", "9", "9"],
                ["LinhTT127", "Tran Thi Linh", "x", "9", "9", "9"],
            ],
        )
    )
    merged = retake.merge(first, second, void=["LinhTT127"])
    assert by_id(merged)["LinhTT127"] == ["LinhTT127", "Tran Thi Linh", "", "", "", ""]
    assert merged.voided == ["LinhTT127"]


def test_the_policy_is_flags(attempts):
    merged = retake.merge(*attempts, cap=8, keep="retake", cap_note="Thi lại: tối đa {cap}.")
    rows = by_id(merged)
    assert rows["LinhTT127"][-1] == "4"
    assert rows["PhuongBV3"][2] == "T1: retake | Thi lại: tối đa 8."


def test_different_papers_lose_their_weights_not_their_scores(tmp_path):
    first = retake.read(grades(tmp_path, "f.csv", [["PhuongBV3", "", "", "2", "2", "2"]]))
    second = retake.read(
        grades(
            tmp_path,
            "r.csv",
            [["PhuongBV3", "", "", "5", "5", "6", "5.4"]],
            tasks=("T1 (30%)", "T2 (30%)", "T3 (40%)"),
        )
    )
    merged = retake.merge(first, second)
    assert merged.headers == ["Std ID", "Name", "Comment", "T1", "T2", "T3", "Total"]
    assert merged.rows == [["PhuongBV3", "", "", "5", "5", "6", "5.4"]]
    assert merged.notes


def test_merge_retake_cli_leaves_its_inputs_alone(tmp_path, attempts):
    first, second = tmp_path / "first.csv", tmp_path / "retake.csv"
    before = first.read_bytes(), second.read_bytes()
    out = tmp_path / "merged.csv"
    argv = ["--no-venv", "assessment", "grade", "merge-retake", "--first", str(first)]
    argv += ["--retake", str(second), "--out", str(out), "--void-ids", "AnhPQ54"]
    assert main(argv) == 0
    assert (first.read_bytes(), second.read_bytes()) == before
    assert read_csv(out)[0] == ["Std ID", "Name", "Comment", "T1 (50%)", "T2 (50%)", "Total"]


# --- Quizzes side by side ----------------------------------------------------


def scores(tmp_path, name, rows):
    path = tmp_path / name
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Std ID", "score"])
        writer.writerows(rows)
    return path


def test_quizzes_line_up_by_roster_with_blanks_for_a_missed_quiz(tmp_path, roster_csv):
    q1 = scores(tmp_path, "q1.csv", [["PhuongBV3", "9.0"], ["LinhTT127", "7.5"]])
    q2 = scores(tmp_path, "q2.csv", [["LinhTT127", "8.0"], ["Stranger1", "5.0"]])
    merged = quiz_merge.merge(
        quiz_merge.parse_inputs([f"FND 01={q1}", f"FND 02={q2}"]), roster_mod.load(roster_csv)
    )
    assert merged.headers == ["No", "ID", "Name", "FND 01", "FND 02"]
    assert merged.rows == [
        ["1", "PhuongBV3", "Bui Van Phuong", "9.0", ""],
        ["2", "LinhTT127", "Tran Thi Linh", "7.5", "8.0"],
    ]
    assert merged.unknown == {"FND 02": ["stranger1"]}


@pytest.mark.parametrize("value", ["no-label.csv", "=q.csv", "Q1="])
def test_a_quiz_needs_a_label_and_a_path(value):
    with pytest.raises(UsageError):
        quiz_merge.parse_inputs([value])
