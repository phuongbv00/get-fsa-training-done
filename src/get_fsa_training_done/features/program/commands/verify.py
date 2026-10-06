"""`get-fsa-training-done program verify` — does this programme reconcile?

Reads a programme directory and reports every place its artifacts disagree.
Each finding names the rule that produced it, so a failure is a lookup in
`references/rules.md` rather than a paragraph to interpret.

Nothing here is hardcoded to a particular programme. Module count, hour and day
totals, the length of a training day, and the number of week and day columns are
all derived from the sources — the reference pipeline this replaces carried them
as constants and only worked for one cohort.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.common.findings import Report

from ..core import contracts as contracts_mod
from ..core import loader
from ..core.checks import crosslink as crosslink_checks
from ..core.checks import program as program_checks
from ..core.checks import topic as topic_checks


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "verify",
        help="check that a programme's curriculum, schedules and syllabi reconcile",
        description=(
            "Read a programme directory and report every place its artifacts "
            "disagree — module totals, schedule minutes, time allocation shares, "
            "assessment counts, and the outcome-standard mapping."
        ),
    )
    parser.add_argument("--program-dir", required=True, help="directory holding curriculum/")
    parser.add_argument("--curriculum", help="the curriculum document, if not found by convention")
    parser.add_argument("--syllabi-dir", help="the syllabi directory, if not curriculum/syllabi")
    parser.add_argument("--topic", help="check one topic code only")
    parser.add_argument(
        "--minutes-per-day",
        type=int,
        help="length of a training day; derived from the TOTAL row by default",
    )
    parser.add_argument(
        "--first-weekday",
        default="mon",
        help="weekday the first day column falls on (default: mon)",
    )
    parser.add_argument(
        "--max-sessions-per-chapter",
        default="2",
        help="how many sessions one chapter may span, or 'inf' (default: 2)",
    )
    parser.add_argument("--pass-mark", type=int, default=6, help="Pass Criteria count (default: 6)")
    parser.add_argument("--creator", help="expected syllabus creator name")
    parser.add_argument(
        "--item-pattern",
        action="append",
        metavar="ITEM=REGEX",
        help="override how an assessment item is matched in the session plan",
    )
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable")
    parser.set_defaults(func=run)


def _max_sessions(value: str) -> float:
    if value.strip().lower() in {"inf", "infinity", "none"}:
        return float("inf")
    try:
        return float(value)
    except ValueError:
        raise UsageError(
            f"--max-sessions-per-chapter expects a number or 'inf', got {value!r}"
        ) from None


def run(args: argparse.Namespace) -> int:
    bundle = loader.load(
        Path(args.program_dir),
        curriculum=Path(args.curriculum).expanduser() if args.curriculum else None,
        syllabi_dir=Path(args.syllabi_dir).expanduser() if args.syllabi_dir else None,
        topic=args.topic,
    )
    report = Report()
    for name in bundle.missing:
        report.error("PRG-P03", name, "file is missing")

    program = bundle.program
    if not args.topic:
        program_checks.check(program, bundle.tables, report, first_weekday=args.first_weekday)

    minutes_per_day = args.minutes_per_day
    if minutes_per_day is None:
        try:
            minutes_per_day = program.minutes_per_day
        except UsageError:
            # PRG-P02 has already reported why; the topic checks that depend on
            # it are skipped rather than measured against a guess.
            minutes_per_day = None

    item_patterns = contracts_mod.parse_overrides(args.item_pattern)
    if minutes_per_day is not None:
        for code, syllabus in sorted(bundle.syllabi.items()):
            topic_checks.check(
                syllabus,
                bundle.schedules.get(code),
                report,
                minutes_per_day=minutes_per_day,
                max_sessions_per_chapter=_max_sessions(args.max_sessions_per_chapter),
                pass_mark=args.pass_mark,
                creator={"name": args.creator} if args.creator else None,
                item_patterns=item_patterns,
            )

    if not args.topic:
        crosslink_checks.check(program, bundle.syllabi, report)

    report.facts["topics"] = len(bundle.syllabi)
    label = f"{program.path.name} ({len(bundle.syllabi)} topics)"
    if args.as_json:
        print(report.as_json(label, strict=args.strict))
        return 0 if report.ok and not (args.strict and report.warnings) else 1
    return report.report(label, strict=args.strict)
