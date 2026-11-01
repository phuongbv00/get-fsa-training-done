"""A module's quizzes: ingest, then score by roster."""

from __future__ import annotations

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.assessment.core.grading import quiz_module
from get_fsa_training_done.features.assessment.core.grading import roster as roster_mod

from .test_quiz_scores import leaderboard, player, read_csv, write_xlsx

HEADER = ",".join(quiz_module.RESULT_HEADERS)


def results(tmp_path, *lines):
    path = tmp_path / "jcf_quiz_results.csv"
    path.write_text("\n".join([HEADER, *lines]) + "\n", encoding="utf-8-sig")
    return path


def grade(*argv):
    return main(["--no-venv", "assessment", "grade", *map(str, argv)])


# --- ingest --------------------------------------------------------------------


def test_ingest_appends_each_source_under_its_quiz_label(tmp_path):
    html = leaderboard(tmp_path, "live.html", [player("PhuongBV3", 36, 1)])
    report = tmp_path / "report.xlsx"
    write_xlsx(
        report,
        [
            ["Nickname", "Qs Answered", "Correct", "Incorrect", "Unattempted"],
            ["LinhTT127", 8, 8, 0, 2],
        ],
    )
    out = tmp_path / "jcf_quiz_results.csv"
    assert (
        grade("quiz-ingest", "--results", out, "--quiz", "JCF 01", "--part", "live", "--html", html)
        == 0
    )
    assert grade("quiz-ingest", "--results", out, "--quiz", "JCF 02", "--xlsx", report) == 0
    assert read_csv(out) == [
        quiz_module.RESULT_HEADERS,
        # A leaderboard gives no unattempted count; the score step supplies it.
        ["JCF 01", "live", "PhuongBV3", "36", "1", "37", ""],
        ["JCF 02", "", "LinhTT127", "8", "0", "8", "2"],
    ]


def test_ingest_refuses_to_append_to_some_other_csv(tmp_path):
    other = tmp_path / "other.csv"
    other.write_text("ID,score\n", encoding="utf-8")
    html = leaderboard(tmp_path, "q.html", [player("PhuongBV3", 1, 1)])
    with pytest.raises(UsageError, match="results CSV"):
        grade("quiz-ingest", "--results", other, "--quiz", "JCF 01", "--html", html)


# --- score ---------------------------------------------------------------------


def test_a_module_scores_by_roster_with_best_attempt_and_blanks(tmp_path, roster_csv):
    path = results(
        tmp_path,
        "JCF 01,live,phuongbv3,20,2,,",
        "JCF 01,HW,PhuongBV3,30,1,,",
        "JCF 01,live,LinhTT127,46,8,,",  # 54 answered: scored out of 54, not 40
        "JCF 02,,LinhTT127,8,0,8,2",  # a report row brings its own unattempted
        "JCF 02,,HieuLX14,10,0,10,0",  # dropped
        "JCF 02,,stranger,5,5,,",
    )
    module = quiz_module.score(
        quiz_module.read_results(path), roster_mod.load(roster_csv), {"": 40}
    )
    assert module.headers == ["No", "ID", "Name", "JCF 01", "JCF 02"]
    assert module.rows == [
        ["1", "PhuongBV3", "Bui Van Phuong", "7.5", ""],
        ["2", "LinhTT127", "Tran Thi Linh", "8.6", "8.0"],
    ]
    assert module.scored == {"JCF 01": 2, "JCF 02": 1}
    assert module.dropped == {"JCF 02": ["HieuLX14"]}
    assert module.unmatched == {"JCF 02": ["stranger"]}


def test_a_quiz_can_have_its_own_question_count(tmp_path, roster_csv):
    path = results(tmp_path, "JCF 01,,PhuongBV3,15,0,,", "JCF 02,,PhuongBV3,15,0,,")
    module = quiz_module.score(
        quiz_module.read_results(path),
        roster_mod.load(roster_csv),
        quiz_module.parse_questions(30, ["JCF 02=20"]),
    )
    assert module.rows[0][3:] == ["5.0", "7.5"]


def test_a_leaderboard_row_without_a_question_count_is_refused(tmp_path, roster_csv):
    path = results(tmp_path, "JCF 01,,PhuongBV3,15,0,,")
    with pytest.raises(UsageError, match="question count"):
        quiz_module.score(quiz_module.read_results(path), roster_mod.load(roster_csv), {})


@pytest.mark.parametrize("value", ["JCF 01", "JCF 01=", "=20", "JCF 01=0", "JCF 01=x"])
def test_questions_for_takes_label_and_count(value):
    with pytest.raises(UsageError):
        quiz_module.parse_questions(40, [value])


def test_quiz_score_command_maps_aliases(tmp_path, roster_csv):
    path = results(tmp_path, "JCF 01,,Linh T,40,0,,")
    out = tmp_path / "jcf_quiz_scores.csv"
    assert (
        grade(
            "quiz-score",
            "--results",
            path,
            "--roster",
            roster_csv,
            "--questions",
            40,
            "--alias",
            "Linh T=LinhTT127",
            "--out",
            out,
        )
        == 0
    )
    assert read_csv(out)[2] == ["2", "LinhTT127", "Tran Thi Linh", "10.0"]
