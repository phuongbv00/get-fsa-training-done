"""The `fsa-training-program` skill: design, verify, and export a training programme.

Owns the programme's *structure* — modules, schedules, the outcome-standard
mapping, per-topic syllabi and their session plans — and the vendor workbooks
those are delivered in. It declares assessment *slots* ("Quiz x2, 10%") but
never authors an instrument: questions, briefs and rubrics belong to
`fsa-training-assessment`, and lecture notes and labs to `fsa-training-material`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ...skillkit import Skill
from .commands import derive, export, verify

PAYLOAD_DIR = Path(__file__).resolve().parent / "payload" / "fsa-training-program"


class Program(Skill):
    def add_worker_parsers(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(self.namespace, help=self.summary)
        sub = parser.add_subparsers(dest="program_command", required=True, metavar="<command>")
        for module in (verify, derive, export):
            module.add_parser(sub)


SKILL = Program(
    name="fsa-training-program",
    namespace="program",
    summary="design and export training curricula (verify, derive, export)",
    payload_dir=PAYLOAD_DIR,
    dep_group="core",
)
