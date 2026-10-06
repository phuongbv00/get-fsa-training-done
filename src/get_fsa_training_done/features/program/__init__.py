"""`program`: design, verify, and export a training programme.

Owns the programme's *structure* — modules, schedules, the outcome-standard
mapping, per-topic syllabi and their session plans — and the vendor workbooks
those are delivered in. It declares assessment *slots* ("Quiz x2, 10%") but
never authors an instrument: questions, briefs and rubrics belong to the
assessment feature, and lecture notes and labs to the material feature.
"""

from __future__ import annotations

import argparse

from .commands import derive, export, verify

NAMESPACE = "program"
SUMMARY = "design and export training curricula (verify, derive, export)"


def add_parsers(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(NAMESPACE, help=SUMMARY)
    sub = parser.add_subparsers(dest="program_command", required=True, metavar="<command>")
    for module in (verify, derive, export):
        module.add_parser(sub)
