"""Structural verification, one module per artifact family."""

from .common import CheckResult

#: The six assessment types, grouped by the shape of what they produce.
LONG_FORM_TYPES = ("short_assignment", "long_assignment", "practice_exam")
QUESTION_SET_TYPES = ("quiz", "theory_exam")
CAPSTONE_TYPES = ("capstone_project",)

#: Question-set types that can also be written: a brief of open-ended
#: questions, a rubric, and (for an exam) an answer template the candidate
#: fills in. Which form is being checked follows from the files given.
WRITTEN_TYPES = QUESTION_SET_TYPES

#: Canonical display order — quiz first, then by increasing scope.
ALL_TYPES = (
    "quiz",
    "short_assignment",
    "long_assignment",
    "theory_exam",
    "practice_exam",
    "capstone_project",
)

__all__ = [
    "ALL_TYPES",
    "CAPSTONE_TYPES",
    "LONG_FORM_TYPES",
    "QUESTION_SET_TYPES",
    "WRITTEN_TYPES",
    "CheckResult",
]
