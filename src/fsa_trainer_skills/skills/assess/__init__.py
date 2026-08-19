"""The `fsa-assess` skill: design and grade FSA training assessments."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...skillkit import Skill
from .commands import emit, grade, levels, render, verify
from .core.pdf import find_chrome

PAYLOAD_DIR = Path(__file__).resolve().parent / "payload" / "fsa-assess"


class Assess(Skill):
    def add_worker_parsers(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(self.namespace, help=self.summary)
        sub = parser.add_subparsers(dest="assess_command", required=True, metavar="<command>")
        for module in (render, verify, emit, grade, levels):
            module.add_parser(sub)

    def doctor_extra(self) -> dict[str, str]:
        return {"chrome": find_chrome() or ""}


SKILL = Assess(
    name="fsa-assess",
    namespace="assess",
    summary="design and grade assessments (render, verify, emit, grade, levels)",
    payload_dir=PAYLOAD_DIR,
    dep_group="core",
)
