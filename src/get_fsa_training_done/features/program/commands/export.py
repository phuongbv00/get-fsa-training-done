"""`get-fsa-training-done program export` — fill the vendor workbook.

The template is edited, not rebuilt: its sheets are rewritten in place and every
other part of the package is copied through untouched, so the form keeps its
logo, its classification label, its print setup, its validations and its
formatting. Reconstructing the file with a spreadsheet library loses those, and
the pipeline this replaces emitted 17 of the template's 35 parts.

The workbook is verified before it is written. Exporting a programme that does
not reconcile produces a document that looks official and states figures that
disagree with each other, which is worse than no document.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import FsaTrainerSkillsError, UsageError
from get_fsa_training_done.features.common.findings import Report

from ..core import csvio
from ..core import syllabus as syllabus_mod
from ..core.checks import topic as topic_checks
from ..core.xlsx import probe as probe_mod
from ..core.xlsx import syllabus_layout as layout
from ..core.xlsx.package import XlsxPackage


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "export",
        help="fill a vendor workbook from the source documents",
        description=(
            "Populate the sheets of a copy of the template, preserving every "
            "other part of the workbook exactly as it was."
        ),
    )
    sub = parser.add_subparsers(dest="export_kind", required=True, metavar="<kind>")

    syllabus = sub.add_parser(
        "syllabus",
        help="one topic's syllabus and session plan",
        description="Write a topic's syllabus, session plan and authorship into the form.",
    )
    syllabus.add_argument("--template", required=True, help="the vendor .xlsx template")
    syllabus.add_argument("--syllabus", required=True, help="the topic's syllabus document")
    syllabus.add_argument("--schedule", help="its ScheduleDetail CSV (default: found alongside)")
    syllabus.add_argument("-o", "--out", help="output workbook (default: <CODE>_Syllabus.xlsx)")
    syllabus.add_argument(
        "--minutes-per-day",
        type=int,
        default=240,
        help="length of a training day, for the pre-export check (default: 240)",
    )
    syllabus.add_argument(
        "--drop-sheet",
        action="append",
        default=None,
        help=f"sheet to remove (default: {layout.IDENTITY_SHEET})",
    )
    syllabus.add_argument(
        "--no-rename-sheets",
        action="store_true",
        help="leave the template's placeholder sheet names alone",
    )
    syllabus.add_argument(
        "--keep-calc-chain",
        action="store_true",
        help="keep xl/calcChain.xml (debugging only; Excel rebuilds it)",
    )
    syllabus.add_argument(
        "--no-verify", action="store_true", help="write even if the sources do not reconcile"
    )
    syllabus.set_defaults(func=run_syllabus)


def run_syllabus(args: argparse.Namespace) -> int:
    syllabus_path = Path(args.syllabus).expanduser()
    syllabus = syllabus_mod.parse(syllabus_path)
    code = syllabus.code or syllabus_path.stem.replace("_Syllabus", "")

    schedule_path = (
        Path(args.schedule).expanduser()
        if args.schedule
        else syllabus_path.with_name(f"{code}_ScheduleDetail.csv")
    )
    schedule_table = csvio.read_table(schedule_path)

    if not args.no_verify:
        report = Report()
        topic_checks.check(
            syllabus,
            schedule_table,
            report,
            minutes_per_day=args.minutes_per_day,
            max_sessions_per_chapter=float("inf"),
        )
        if not report.ok:
            print(f"FAIL: {syllabus_path.name} does not reconcile with its session plan")
            for finding in report.errors:
                print(f"ERROR: {finding.line()}")
            print("nothing was written; pass --no-verify to export anyway")
            return 1

    rows = schedule_table.rows
    if len(rows) > layout.MAX_DATA_ROWS:
        raise FsaTrainerSkillsError(
            f"{schedule_path.name} has {len(rows)} rows; the template's band holds "
            f"{layout.MAX_DATA_ROWS}",
            hint=(
                "the summary block sits immediately below the band, so more rows would "
                "overwrite it — split the topic or widen the template"
            ),
        )

    package = XlsxPackage(Path(args.template).expanduser())
    probe_mod.require(package, layout.REQUIRED_SHEETS, layout.EXPECTATIONS)

    schedule_sheet = package.sheet(layout.SCHEDULE_SHEET)
    syllabus_sheet = package.sheet(layout.SYLLABUS_SHEET)
    author_sheet = package.sheet(layout.AUTHOR_SHEET)

    schedule_name = layout.SCHEDULE_SHEET if args.no_rename_sheets else f"{code}_ScheduleDetail"
    sessions = len({row.get("Session", "") for row in rows if row.get("Session", "").strip()})

    layout.write_schedule(schedule_sheet, rows)
    layout.write_syllabus(
        package,
        syllabus_sheet,
        schedule_sheet,
        syllabus,
        schedule_sheet_name=schedule_name,
        session_count=sessions,
    )
    layout.write_authors(package, author_sheet, syllabus)

    package.write_sheet(layout.SCHEDULE_SHEET, schedule_sheet)
    package.write_sheet(layout.SYLLABUS_SHEET, syllabus_sheet)
    package.write_sheet(layout.AUTHOR_SHEET, author_sheet)

    if not args.no_rename_sheets:
        package.rename_sheet(layout.SCHEDULE_SHEET, schedule_name)
        package.rename_sheet(layout.SYLLABUS_SHEET, f"{code}_Syllabus")

    for name in args.drop_sheet if args.drop_sheet is not None else [layout.IDENTITY_SHEET]:
        package.drop_sheet(name)

    package.force_full_recalc()
    if not args.keep_calc_chain:
        package.drop_calc_chain()

    out = Path(args.out).expanduser() if args.out else syllabus_path.with_suffix(".xlsx")
    if out.resolve() == Path(args.template).expanduser().resolve():
        raise UsageError("refusing to overwrite the template; pass -o for the output")
    package.save(out)

    kept = len(package.parts)
    print(
        f"PASS: wrote {out} ({len(rows)} session rows, {sessions} sessions, "
        f"{kept} workbook parts preserved)"
    )
    return 0
