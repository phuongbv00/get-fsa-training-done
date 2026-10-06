"""The grading pipeline: preprocess, plan, aggregate, retakes, quiz scores, cheat
checks.

Every module here takes explicit paths. The original scripts defaulted
`--classes-root` to `data/classes` and `--results-root` to `data/results`, both
relative, which silently assumed the current directory was one particular
repository root. Nothing here assumes a layout: the caller says where things are.
"""

from . import (
    aggregate,
    ai_cheat,
    batches,
    plagiarism,
    preprocess,
    quiz_merge,
    quiz_scores,
    retake,
    roster,
)

__all__ = [
    "aggregate",
    "ai_cheat",
    "batches",
    "plagiarism",
    "preprocess",
    "quiz_merge",
    "quiz_scores",
    "retake",
    "roster",
]
