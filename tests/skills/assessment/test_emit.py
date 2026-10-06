"""Byte-exactness of the derived import files.

The fixtures are excerpts of artifacts that were hand-authored and are in real
use, so these are correctness tests rather than snapshots of our own output.
Each platform has at least one convention that is invisible until an import
fails, and every one of them is asserted here.
"""

from __future__ import annotations

import json

import pytest

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.skills.assessment.core.emit import blooket, coderbyte, master

from .conftest import FIXTURES


def test_blooket_matches_real_export():
    questions = master.read(FIXTURES / "question_set" / "quiz_master.csv")
    produced = blooket.render(questions)
    assert produced == (FIXTURES / "question_set" / "quiz_blooket.csv").read_bytes()


def test_blooket_title_row_has_eight_fields():
    # Blooket sniffs the delimiter from this row. A single-cell title row makes
    # it guess wrong, and the failure surfaces later as "Invalid Opening Quote"
    # on the first correctly quoted field.
    questions = master.read(FIXTURES / "question_set" / "quiz_master.csv")
    first_line = blooket.render(questions).split(b"\r\n")[0]
    assert first_line == b"Blooket Import Template,,,,,,,"
    assert first_line.count(b",") == 7


def test_blooket_uses_crlf_and_no_bom():
    questions = master.read(FIXTURES / "question_set" / "quiz_master.csv")
    produced = blooket.render(questions)
    assert not produced.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in produced
    assert produced.replace(b"\r\n", b"").count(b"\n") == 0


def test_coderbyte_matches_real_export():
    questions = master.read(FIXTURES / "question_set" / "theory_master.csv")
    produced = coderbyte.render(questions)
    assert produced == (FIXTURES / "question_set" / "theory_coderbyte.json").read_bytes()


def test_coderbyte_puts_the_correct_answer_first():
    questions = master.read(FIXTURES / "question_set" / "theory_master.csv")
    built = coderbyte.build(questions)
    for question, entry in zip(questions, built["mc_questions"]):
        if not question.is_multi:
            assert entry["answers"][0] == question.option(question.correct[0])
            assert "correctAnswers" not in entry


def test_coderbyte_multi_answer_always_leads_with_a_correct_option():
    """Coderbyte treats index 0 as correct whether or not it is listed.

    Its own template proves it: `correctAnswers: ["2", "3"]` over answers
    `["I am correct", "Wrong 2", "Will be correct", "Will be correct"]` means
    0, 2 and 3 are correct. So leaving a wrong option at index 0 while listing
    the real ones silently marks that wrong option correct.
    """
    questions = master.read(FIXTURES / "question_set" / "theory_master.csv")
    source = questions[0]
    # Options 2 and 4 are correct; option 1 is not.
    patched = [
        master.Question(
            number=source.number,
            unit=source.unit,
            bloom=source.bloom,
            difficulty=source.difficulty,
            text=source.text,
            options=source.options,
            correct=[2, 4],
            time_limit=source.time_limit,
            note=source.note,
        )
    ]
    entry = coderbyte.build(patched)["mc_questions"][0]

    assert entry["allRequired"] is True
    assert "0" in entry["correctAnswers"], "a correct option must lead and be listed"
    assert entry["answers"][0] == source.option(2)

    marked = {entry["answers"][int(i)] for i in entry["correctAnswers"]}
    assert marked == {source.option(2), source.option(4)}
    # The option that is not correct must not end up marked.
    assert source.option(1) not in marked


def test_coderbyte_multi_answer_handles_duplicate_option_text():
    """Positions are mapped through the permutation, not looked up by text."""
    questions = master.read(FIXTURES / "question_set" / "theory_master.csv")
    source = questions[0]
    patched = [
        master.Question(
            number=source.number,
            unit=source.unit,
            bloom=source.bloom,
            difficulty=source.difficulty,
            text=source.text,
            options=["same", "same", "other", "another"],
            correct=[3, 4],
            time_limit=source.time_limit,
            note=source.note,
        )
    ]
    entry = coderbyte.build(patched)["mc_questions"][0]
    assert entry["answers"][0] == "other"
    marked = sorted(entry["answers"][int(i)] for i in entry["correctAnswers"])
    assert marked == ["another", "other"]


def test_master_reader_rejects_a_wrong_header(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("No,Question,Answer\n1,x,y\n", encoding="utf-8")
    with pytest.raises(UsageError, match="header"):
        master.read(bad)


def test_master_reader_rejects_an_out_of_range_key(tmp_path, quiz_master_rows):
    rows = quiz_master_rows
    rows[1][9] = "9"
    bad = tmp_path / "bad.csv"
    bad.write_text("\n".join(",".join(f'"{c}"' for c in row) for row in rows), encoding="utf-8")
    with pytest.raises(UsageError, match="outside 1-"):
        master.read(bad)


def test_coderbyte_output_is_valid_json():
    questions = master.read(FIXTURES / "question_set" / "theory_master.csv")
    parsed = json.loads(coderbyte.render(questions))
    assert len(parsed["mc_questions"]) == len(questions)
