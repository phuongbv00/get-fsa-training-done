"""The `fsa-training-assessment` skill: design and grade FSA training assessments."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...skillkit import Skill
from .commands import emit, grade, levels, render, sprint_kit, verify

PAYLOAD_DIR = Path(__file__).resolve().parent / "payload" / "fsa-training-assessment"


class Assessment(Skill):
    def add_worker_parsers(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(self.namespace, help=self.summary)
        sub = parser.add_subparsers(dest="assessment_command", required=True, metavar="<command>")
        for module in (render, verify, emit, sprint_kit, grade, levels):
            module.add_parser(sub)

    def doctor_extra(self) -> dict[str, str]:
        """Nothing external to report.

        `render` embeds its own fonts and `grade preprocess` reads archives with
        the standard library, so the only optional binary left is the `.rar`
        extractor, which `doctor` looks for on its own.
        """
        return {}


SKILL = Assessment(
    name="fsa-training-assessment",
    namespace="assessment",
    summary="design and grade assessments (render, verify, emit, sprint-kit, grade, levels)",
    payload_dir=PAYLOAD_DIR,
    dep_group="core",
    previous_names=("fsa-assess",),
)
