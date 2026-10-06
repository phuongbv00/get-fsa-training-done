"""`material`: the teaching material a session plan calls for.

Owns lecture notes, module handbooks, appendices and lab guides. It never writes
a quiz, a rubric or a schedule row: a session's `Training Materials` cell names
the file that serves it, and producing *that* file is this feature's job while
the slot itself belongs to the program feature and the assessment instruments
to the assessment feature.
"""

from __future__ import annotations

import argparse

from .commands import coverage, derive, verify

NAMESPACE = "material"
SUMMARY = "write and check teaching material (verify, coverage, derive)"


def add_parsers(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(NAMESPACE, help=SUMMARY)
    sub = parser.add_subparsers(dest="material_command", required=True, metavar="<command>")
    for module in (verify, coverage, derive):
        module.add_parser(sub)
