"""Shared vocabulary for the structural verifiers.

These checks cover machine-verifiable *shape* only — whether the files hold
together, whether the numbers add up, whether the bytes will survive an import.
Whether a question is any good is a judgement call and belongs to the
verifier-agent prompts the skill runs afterwards.
"""

from __future__ import annotations

import re
from pathlib import Path

#: The instructor-only source of truth for every question-set assessment.
#: Quizzes and theory exams both use this exact header.
MASTER_COLUMNS = [
    "No",
    "Unit/Lecture",
    "Bloom Level",
    "Difficulty",
    "Question",
    "Answer 1",
    "Answer 2",
    "Answer 3",
    "Answer 4",
    "Correct Answer(s)",
    "Time Limit (sec)",
    "Note",
]

BLOOKET_COLUMNS = [
    "Question #",
    "Question Text",
    "Answer 1",
    "Answer 2",
    "Answer 3 (Optional)",
    "Answer 4 (Optional)",
    "Time Limit (sec) (Max: 300 seconds)",
    "Correct Answer(s) (Only include Answer #)",
]

DEFAULT_TIME_MAP = {"Easy": "5", "Medium": "10", "Hard": "20"}

#: Blooket caps a question's timer here.
MAX_TIME_LIMIT_SECONDS = 300

# Both Blooket and Coderbyte parse imported text as markup, so anything shaped
# like a tag — <CartPanel />, </>, List<String> — is swallowed and never reaches
# the learner. The slash in the character class catches JSX closing and
# self-closing forms. Language operators (->, >=, <=, SQL <>) stay legal because
# they always have whitespace around them.
ANGLE_BRACKET_NEXT_TO_TEXT = re.compile(r"(?<=[A-Za-z0-9_$?/])(?:<|>)|(?:<|>)(?=[A-Za-z0-9_$?/])")
ANGLE_MESSAGE = (
    "angle bracket touches an identifier or slash and will be read as a tag; "
    "name the element in prose ('a CartPanel element', 'a JSX fragment') or "
    "space every bracket ('List < String >', '< CartPanel / >')"
)

#: Neither platform renders Markdown; a backtick either breaks the import or
#: shows up literally on the learner's screen.
BACKTICK = "`"
BACKTICK_MESSAGE = (
    "backtick in question or answer text; Blooket and Coderbyte render plain "
    "text only — drop the backticks around code fragments"
)


class CheckResult:
    """Accumulates findings. Errors fail the run; warnings are advisory."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: CheckResult) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def report(self, label: str) -> int:
        if self.errors:
            print(f"FAIL: {label}")
            for error in self.errors:
                print(f"ERROR: {error}")
        else:
            print(f"PASS: {label}")
        for warning in self.warnings:
            print(f"WARNING: {warning}")
        return 1 if self.errors else 0


def read_text(path: Path, result: CheckResult, *, label: str = "file") -> str:
    if not path.exists():
        result.error(f"Missing {label}: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def normalize_name(value: str) -> str:
    """Fold a task or question name for comparison across two documents."""
    value = value.strip().lower()
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def parse_time_map(value: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for part in value.split(","):
        if not part.strip():
            continue
        key, separator, mapped = part.partition("=")
        if not separator:
            raise ValueError(f"invalid --time-map entry: {part!r}")
        mapping[key.strip()] = mapped.strip()
    return mapping


def check_import_safe_text(text: str, where: str, result: CheckResult) -> None:
    """Reject the two things that silently corrupt a platform import."""
    if BACKTICK in text:
        result.error(f"{where}: {BACKTICK_MESSAGE}")
    if ANGLE_BRACKET_NEXT_TO_TEXT.search(text):
        result.error(f"{where}: {ANGLE_MESSAGE}")


def parse_correct_answers(
    value: str,
    question_no: str,
    result: CheckResult,
    *,
    max_option: int = 4,
) -> list[int]:
    """Parse the 1-based `Correct Answer(s)` cell into option numbers."""
    answers: list[int] = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            number = int(raw)
        except ValueError:
            result.error(f"Question {question_no}: invalid correct answer {raw!r}")
            continue
        if number < 1 or number > max_option:
            result.error(f"Question {question_no}: correct answer {number} outside 1-{max_option}")
            continue
        answers.append(number)
    if not answers:
        result.error(f"Question {question_no}: missing correct answer")
    return answers
