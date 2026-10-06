"""`assessment`: design and grade FSA training assessments."""

from __future__ import annotations

import argparse

from .commands import emit, grade, levels, render, sprint_kit, verify

NAMESPACE = "assessment"
SUMMARY = "design and grade assessments (render, verify, emit, sprint-kit, grade, levels)"


def add_parsers(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(NAMESPACE, help=SUMMARY)
    sub = parser.add_subparsers(dest="assessment_command", required=True, metavar="<command>")
    for module in (render, verify, emit, sprint_kit, grade, levels):
        module.add_parser(sub)
