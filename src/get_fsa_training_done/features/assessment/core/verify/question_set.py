"""Master CSV verification, plus regression checks on the derived import files.

Since `get-fsa-training-done assessment emit` now generates the Blooket CSV and Coderbyte JSON from
the master, the checks against those files are cheap regression tests rather
than the correctness safety-net they used to be. They stay because a
hand-edited import file is exactly the kind of thing that silently diverges.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from get_fsa_training_done.features.common.levels import Level

from . import calibration
from .common import (
    BLOOKET_COLUMNS,
    MASTER_COLUMNS,
    MAX_TIME_LIMIT_SECONDS,
    CheckResult,
    check_import_safe_text,
    normalize_name,
    parse_correct_answers,
)

_STRAY_LINE_ENDING = re.compile(rb"(?<!\r)\n|\r(?!\n)")


def read_master(path: Path, result: CheckResult) -> list[dict[str, str]]:
    if not path.exists():
        result.error(f"Missing master CSV: {path}")
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != MASTER_COLUMNS:
            result.error(
                "Master CSV header does not match the expected 12 columns.\n"
                f"       expected: {','.join(MASTER_COLUMNS)}\n"
                f"       found:    {','.join(reader.fieldnames or [])}"
            )
            return []
        return list(reader)


def verify_master(
    rows: list[dict[str, str]],
    time_map: dict[str, str],
    result: CheckResult,
    *,
    expect_count: int | None = None,
) -> None:
    if not rows:
        result.error("Master CSV has no questions")
        return
    if expect_count is not None and len(rows) != expect_count:
        result.error(f"Master CSV has {len(rows)} questions, expected {expect_count}")

    seen: dict[str, str] = {}
    for expected_no, row in enumerate(rows, start=1):
        no = row["No"].strip()
        if no != str(expected_no):
            result.error(f"Question numbering: expected {expected_no}, found {no!r}")

        for column in ("Unit/Lecture", "Bloom Level", "Difficulty", "Question"):
            if not row[column].strip():
                result.error(f"Question {no}: missing {column}")
        for index in range(1, 5):
            if not row[f"Answer {index}"].strip():
                result.error(f"Question {no}: missing Answer {index}")

        for column in ("Question", "Answer 1", "Answer 2", "Answer 3", "Answer 4"):
            check_import_safe_text(row[column], f"Question {no}, {column}", result)

        parse_correct_answers(row["Correct Answer(s)"], no, result)

        difficulty = row["Difficulty"].strip()
        expected_time = time_map.get(difficulty)
        if expected_time is None:
            result.error(
                f"Question {no}: unknown difficulty {difficulty!r}; "
                f"the time map covers {', '.join(sorted(time_map))}"
            )
        elif row["Time Limit (sec)"].strip() != expected_time:
            result.error(
                f"Question {no}: time limit {row['Time Limit (sec)'].strip()!r}, "
                f"expected {expected_time} for {difficulty}"
            )

        limit = row["Time Limit (sec)"].strip()
        if limit.isdigit() and int(limit) > MAX_TIME_LIMIT_SECONDS:
            result.error(
                f"Question {no}: time limit {limit}s exceeds the "
                f"{MAX_TIME_LIMIT_SECONDS}s platform maximum"
            )

        key = normalize_name(row["Question"])
        if key in seen:
            result.error(f"Question {no}: duplicate of question {seen[key]}")
        else:
            seen[key] = no


def verify_coderbyte(path: Path, master: list[dict[str, str]], result: CheckResult) -> None:
    if not path.exists():
        result.error(f"Missing Coderbyte JSON: {path}")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.error(f"Coderbyte JSON is not valid JSON: {exc}")
        return

    questions = data.get("mc_questions")
    if not isinstance(questions, list):
        result.error("Coderbyte JSON must have a top-level 'mc_questions' list")
        return
    if len(questions) != len(master):
        result.error(f"Coderbyte has {len(questions)} questions, master has {len(master)}")

    for index, (row, question) in enumerate(zip(master, questions, strict=False), start=1):
        if not isinstance(question, dict):
            result.error(f"Coderbyte question {index}: must be an object")
            continue
        if question.get("question") != row["Question"]:
            result.error(f"Coderbyte question {index}: question text differs from the master")

        answers = question.get("answers")
        if not isinstance(answers, list) or len(answers) < 4:
            result.error(f"Coderbyte question {index}: expected at least 4 answers")
            continue
        if any(not isinstance(answer, str) or not answer.strip() for answer in answers):
            result.error(f"Coderbyte question {index}: answers must be non-empty strings")
            continue

        for text in [question.get("question", ""), *answers]:
            if isinstance(text, str):
                check_import_safe_text(text, f"Coderbyte question {index}", result)

        correct = parse_correct_answers(row["Correct Answer(s)"], row["No"], result)
        if len(correct) == 1:
            # Coderbyte's convention for single-answer questions is that the
            # first option is the correct one.
            if answers[0] != row[f"Answer {correct[0]}"]:
                result.error(f"Coderbyte question {index}: the correct answer must come first")
            if question.get("correctAnswers"):
                result.warn(
                    f"Coderbyte question {index}: single-answer question also sets correctAnswers"
                )
        else:
            indices = question.get("correctAnswers")
            if not isinstance(indices, list):
                result.error(f"Coderbyte question {index}: multi-answer needs correctAnswers")
            else:
                listed = [str(value) for value in indices]
                if "0" not in listed:
                    # Coderbyte counts index 0 as correct whether or not it is
                    # listed, so a multi-answer question that does not lead with
                    # a correct option silently marks a wrong one correct.
                    result.error(
                        f'Coderbyte question {index}: correctAnswers must include "0" — '
                        "Coderbyte treats the first option as correct, so a correct option "
                        "has to lead and be listed among the indices"
                    )
                marked: set[str] | None = set()
                for value in listed:
                    try:
                        marked.add(answers[int(value)])
                    except (ValueError, IndexError):
                        result.error(
                            f"Coderbyte question {index}: correctAnswers entry {value!r} "
                            "is not a valid 0-based index into answers"
                        )
                        marked = None
                        break
                if marked is not None:
                    expected = {row[f"Answer {n}"] for n in correct}
                    if marked != expected:
                        result.error(
                            f"Coderbyte question {index}: the options marked correct do not "
                            "match the master's answer key"
                        )
            if question.get("allRequired") is not True:
                result.error(f"Coderbyte question {index}: allRequired must be true")


def verify_blooket(path: Path, master: list[dict[str, str]], result: CheckResult) -> None:
    if not path.exists():
        result.error(f"Missing Blooket CSV: {path}")
        return
    try:
        raw = path.read_bytes()
    except OSError as exc:
        result.error(f"Cannot read the Blooket CSV: {exc}")
        return

    if raw.startswith(b"\xef\xbb\xbf"):
        result.error("Blooket CSV must be UTF-8 without a BOM")
    if _STRAY_LINE_ENDING.search(raw):
        result.error("Blooket CSV must use CRLF line endings throughout")

    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle, strict=True))
    except csv.Error as exc:
        result.error(f"Blooket CSV has invalid RFC 4180 quoting: {exc}")
        return

    header_index = next((i for i, row in enumerate(rows) if row == BLOOKET_COLUMNS), None)
    if header_index is None:
        result.error("Blooket CSV is missing the expected import header row")
        return

    # Blooket sniffs the delimiter from the title row. A single-cell title row
    # makes it guess wrong, and later valid quoted fields then fail with
    # "Invalid Opening Quote" — hence the seven trailing empty fields.
    expected_title = ["Blooket Import Template", "", "", "", "", "", "", ""]
    if header_index != 1 or not rows or rows[0] != expected_title:
        result.error(
            "Blooket CSV must open with the eight-field title row "
            "'Blooket Import Template,,,,,,,' followed by the import header"
        )

    data_rows = rows[header_index + 1 :]
    if len(data_rows) != len(master):
        result.error(f"Blooket has {len(data_rows)} rows, master has {len(master)}")

    for index, (row_master, row) in enumerate(zip(master, data_rows, strict=False), start=1):
        if len(row) != len(BLOOKET_COLUMNS):
            result.error(f"Blooket row {index}: expected {len(BLOOKET_COLUMNS)} columns")
            continue
        if row[1] != row_master["Question"]:
            result.error(f"Blooket row {index}: question text differs from the master")
        if any(not row[column].strip() for column in range(2, 6)):
            result.error(f"Blooket row {index}: expected 4 non-empty answer options")
        for answer_index in range(1, 5):
            if row[answer_index + 1] != row_master[f"Answer {answer_index}"]:
                result.error(f"Blooket row {index}: Answer {answer_index} differs from the master")
        for offset, text in enumerate(row[1:6], start=2):
            check_import_safe_text(text, f"Blooket row {index}, column {offset}", result)
        if row[6] != row_master["Time Limit (sec)"]:
            result.error(f"Blooket row {index}: time limit differs from the master")
        if row[7] != row_master["Correct Answer(s)"]:
            result.error(f"Blooket row {index}: correct answer differs from the master")


def verify(
    *,
    master_path: str | None,
    blooket_path: str | None,
    coderbyte_path: str | None,
    time_map: dict[str, str],
    expect_count: int | None,
    result: CheckResult,
    level: Level | None = None,
) -> list[dict[str, str]]:
    if not master_path:
        result.error("Question-set verification requires --master")
        return []

    rows = read_master(Path(master_path), result)
    verify_master(rows, time_map, result, expect_count=expect_count)
    if level is not None:
        calibration.check_question_set(rows, level, result)

    if coderbyte_path:
        verify_coderbyte(Path(coderbyte_path), rows, result)
    if blooket_path:
        verify_blooket(Path(blooket_path), rows, result)
    return rows
