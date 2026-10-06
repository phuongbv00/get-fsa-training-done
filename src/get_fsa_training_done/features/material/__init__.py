"""The `fsa-training-material` skill: the teaching material a session plan calls for.

Owns lecture notes, module handbooks, appendices and lab guides. It never writes
a quiz, a rubric or a schedule row: a session's `Training Materials` cell names
the file that serves it, and producing *that* file is this skill's job while the
slot itself belongs to `fsa-training-program` and the assessment instruments to
`fsa-training-assessment`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ...skillkit import Skill
from .commands import coverage, derive, verify

PAYLOAD_DIR = Path(__file__).resolve().parent / "payload" / "fsa-training-material"


class Material(Skill):
    def add_worker_parsers(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(self.namespace, help=self.summary)
        sub = parser.add_subparsers(dest="material_command", required=True, metavar="<command>")
        for module in (verify, coverage, derive):
            module.add_parser(sub)


SKILL = Material(
    name="fsa-training-material",
    namespace="material",
    summary="write and check teaching material (verify, coverage, derive)",
    payload_dir=PAYLOAD_DIR,
    dep_group="core",
)
