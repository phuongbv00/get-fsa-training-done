"""`get-fsa-training-done program derive` — compute what must not be typed.

Two targets, both the same idea as the assessment skill's `emit`: a table that
summarises another file is derived from it, so the two cannot drift.

    derive allocation   section 8 of a syllabus, from its session plan
    derive skeleton     the four programme CSVs, from the module table
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import GftdError, UsageError

from ..core import csvio
from ..core import program as program_mod
from ..core import syllabus as syllabus_mod
from ..core.derive import allocation, skeleton


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "derive",
        help="compute the tables that are summaries of other files",
        description=(
            "Derive a syllabus's Time Allocation from its session plan, or the "
            "programme CSV skeletons from the module table."
        ),
    )
    sub = parser.add_subparsers(dest="derive_target", required=True, metavar="<target>")

    alloc = sub.add_parser(
        "allocation",
        help="section 8 of a syllabus, from its session plan",
        description=(
            "Compute each delivery type's share of the session plan. Printed by "
            "default; --write patches the syllabus, --check fails when it is stale."
        ),
    )
    alloc.add_argument("--schedule", required=True, help="the topic's ScheduleDetail CSV")
    alloc.add_argument("--syllabus", help="the syllabus to patch or check")
    alloc.add_argument(
        "--minutes-per-day",
        type=int,
        help="length of a training day, used to restate Days (default: leave Days alone)",
    )
    mode = alloc.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="patch the syllabus in place")
    mode.add_argument("--check", action="store_true", help="exit 1 if the syllabus is stale")
    alloc.set_defaults(func=run_allocation)

    skel = sub.add_parser(
        "skeleton",
        help="the four programme CSVs, from the module table",
        description=(
            "Write the header row and one row per module for each programme CSV. "
            "What the module table cannot determine is left blank to fill in."
        ),
    )
    skel.add_argument("--curriculum", required=True, help="the curriculum document")
    skel.add_argument("--out-dir", required=True, help="where to write the CSVs")
    skel.add_argument(
        "--kind",
        default="all",
        choices=("all", *skeleton.BUILDERS),
        help="which CSV to write (default: all)",
    )
    skel.add_argument("--weeks", type=int, help="week columns (default: derived from the days)")
    skel.add_argument("--days", type=int, help="day columns (default: derived from the days)")
    skel.add_argument("--ost-rows", type=int, default=0, help="blank outcome rows to stub")
    skel.add_argument("--force", action="store_true", help="overwrite existing files")
    skel.set_defaults(func=run_skeleton)


def run_allocation(args: argparse.Namespace) -> int:
    schedule = csvio.read_table(Path(args.schedule).expanduser())
    if (args.write or args.check) and not args.syllabus:
        raise UsageError("--write and --check need --syllabus")

    days = None
    if args.minutes_per_day:
        days = allocation.days_for(schedule.rows, args.minutes_per_day)
    elif args.syllabus:
        # The length of a training day is a programme-level fact this command
        # does not have, so Days is preserved rather than recomputed.
        days = syllabus_mod.parse(Path(args.syllabus).expanduser()).days or None

    body = allocation.render(schedule.rows, days=days)

    if not args.syllabus:
        print(body)
        return 0

    path = Path(args.syllabus).expanduser()
    original = path.read_text(encoding="utf-8")
    updated = allocation.patch(original, body)

    if args.check:
        if updated != original:
            print(f"FAIL: {path.name} does not match its session plan")
            print(body)
            return 1
        print(f"PASS: {path.name} matches its session plan")
        return 0

    if args.write:
        if updated == original:
            print(f"PASS: {path.name} already matches its session plan")
            return 0
        path.write_text(updated, encoding="utf-8")
        print(f"PASS: rewrote section 8 of {path.name}")
        return 0

    print(body)
    return 0


def run_skeleton(args: argparse.Namespace) -> int:
    curriculum = Path(args.curriculum).expanduser()
    program = program_mod.parse(curriculum)
    if not program.modules:
        raise UsageError(f"{curriculum.name} has no module table to derive from")

    code = curriculum.name
    for suffix in ("_TrainingProgramCurriculum.md",):
        if code.endswith(suffix):
            code = code[: -len(suffix)]

    weeks = args.weeks or skeleton.week_count(program.total_days)
    days = args.days or skeleton.day_column_count(program.total_days)

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    kinds = list(skeleton.BUILDERS) if args.kind == "all" else [args.kind]
    written = []
    for kind in kinds:
        name, build = skeleton.BUILDERS[kind]
        target = out_dir / f"{code}_{name}"
        if target.exists() and not args.force:
            raise GftdError(
                f"{target} already exists",
                hint="pass --force to overwrite it",
            )
        target.write_text(build(program, weeks, days, args.ost_rows), encoding="utf-8")
        written.append(target)

    print(
        f"PASS: wrote {len(written)} file(s) for {len(program.modules)} modules "
        f"({weeks} week columns, {days} day columns)"
    )
    for path in written:
        print(f"  {path}")
    return 0
