"""`get-fsa-training-done material coverage` — does the material the plan asks for exist?

The cross-skill check. A session plan's materials column names the file that
serves each session; this reports both directions — what is promised and
missing, and what is present and unscheduled.

It reads the plan by column name and does not enforce its schema. That belongs
to `get-fsa-training-done program verify`, and duplicating it here would give two
skills two opinions about one file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.findings import Report

from ..core import coverage as coverage_mod
from ..core.grammar import OBJECTIVE_CODE


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "coverage",
        help="cross-check a module's materials against its session plan",
        description=(
            "Report every material a session plan names that does not exist, "
            "and every file present that no session uses."
        ),
    )
    parser.add_argument("--schedule", required=True, help="the topic's ScheduleDetail CSV")
    parser.add_argument("--dir", required=True, dest="directory", help="the materials folder")
    parser.add_argument("--syllabus", help="the topic syllabus, to check objective codes")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    schedule = Path(args.schedule).expanduser()
    directory = Path(args.directory).expanduser()
    demands = coverage_mod.read_demands(schedule)
    report = Report()

    defined = None
    if args.syllabus:
        text = Path(args.syllabus).expanduser().read_text(encoding="utf-8")
        start = text.find("### 6. Course Objectives")
        end = text.find("### 7. Topic Outline", start if start >= 0 else 0)
        defined = set(OBJECTIVE_CODE.findall(text[start:end] if start >= 0 else ""))

    facts = coverage_mod.check(demands, directory, report, defined_objectives=defined)
    coverage_mod.check_objectives(demands, directory, report)
    report.facts.update(facts)

    label = f"{schedule.name} against {directory}"
    if args.as_json:
        print(report.as_json(label, strict=args.strict))
        return 0 if report.ok and not (args.strict and report.warnings) else 1
    return report.report(label, strict=args.strict)
