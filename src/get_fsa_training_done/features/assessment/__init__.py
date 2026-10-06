"""`assessment`: design and grade FSA training assessments."""

from __future__ import annotations

import argparse

from .commands import emit, grade, levels, render, sandbox, sprint_kit, verify

NAMESPACE = "assessment"
SUMMARY = "design and grade assessments (render, verify, emit, sprint-kit, grade, levels, sandbox)"


def add_parsers(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(NAMESPACE, help=SUMMARY)
    sub = parser.add_subparsers(dest="assessment_command", required=True, metavar="<command>")
    for module in (render, verify, emit, sprint_kit, grade, levels, sandbox):
        module.add_parser(sub)


def doctor_extra() -> dict[str, str]:
    """Docker is optional: only `sandbox` uses it."""
    from .core import sandbox as sandbox_core

    return {"docker (sandbox)": sandbox_core.docker_path()}
