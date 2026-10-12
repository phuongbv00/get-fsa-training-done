"""`gftd material handout` — gather what a trainee is handed.

The decks', the lecture note's and the labs' PDFs, copied into one folder to
send; a deck's `.pptx` stays with the trainer. A document with no PDF, or one
older than its HTML, is refused rather than handed out stale.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.common.findings import Report

from ..core import handout as handout_mod


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "handout",
        help="copy the slides', lecture note's and labs' PDFs into the folder sent to trainees",
        description=(
            "Copy every deck, lecture note, lab and worksheet PDF of a module into one "
            "folder. A deck's .pptx is the trainer's; a missing or stale PDF is reported."
        ),
    )
    parser.add_argument("--dir", required=True, dest="directory", help="the materials folder")
    parser.add_argument(
        "--out",
        help=f"the folder to fill (default: <dir>/{handout_mod.DEFAULT_FOLDER})",
    )
    parser.add_argument(
        "--prune", action="store_true", help="remove files in it that are not part of the hand-out"
    )
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    directory = Path(args.directory).expanduser()
    if not directory.is_dir():
        raise UsageError(f"not a folder: {directory}")
    out = Path(args.out).expanduser() if args.out else directory / handout_mod.DEFAULT_FOLDER
    report = Report()
    report.facts.update(handout_mod.build(directory, out, report, prune=args.prune))

    label = f"hand-out in {out}"
    if args.as_json:
        print(report.as_json(label, strict=args.strict))
        return 0 if report.ok and not (args.strict and report.warnings) else 1
    return report.report(label, strict=args.strict)
