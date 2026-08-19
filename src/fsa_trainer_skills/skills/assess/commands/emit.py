"""`fsa-trainer-skills assess emit` — derive delivery artifacts from the master question CSV.

The model authors one file. Everything a platform actually imports is generated
from it, so the import files cannot drift from the answer key, and the format
traps (Blooket's eight-field title row, Coderbyte's correct-answer-first
convention) are handled once here rather than restated in every workflow.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..core.emit import blooket, coderbyte, master

FORMATS = ("blooket", "coderbyte")

DEFAULT_SUFFIX = {
    "blooket": "_blooket.csv",
    "coderbyte": "_coderbyte.json",
}


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "emit",
        help="generate platform import files from a master question CSV",
        description=(
            "Derive a delivery artifact from the master CSV. Never hand-write these — "
            "regenerate them, so the master stays the single source of truth."
        ),
    )
    parser.add_argument("emit_format", choices=list(FORMATS), metavar="format")
    parser.add_argument("--master", required=True, help="master question CSV")
    parser.add_argument("-o", "--out", help="output path (default: derived from the master name)")
    parser.set_defaults(func=run)


def _default_out(master_path: Path, emit_format: str) -> Path:
    return master_path.with_name(master_path.stem + DEFAULT_SUFFIX[emit_format])


def run(args: argparse.Namespace) -> int:
    master_path = Path(args.master).expanduser()
    questions = master.read(master_path)
    out = Path(args.out).expanduser() if args.out else _default_out(master_path, args.emit_format)

    if args.emit_format == "blooket":
        count = blooket.write(questions, out)
        notes = blooket.warnings(questions)
    else:
        count = coderbyte.write(questions, out)
        notes = coderbyte.warnings(questions)

    size_kb = out.stat().st_size / 1024
    print(f"PASS: wrote {out} ({count} questions, {size_kb:.0f} KB)")
    for note in notes:
        print(f"WARNING: {note}")
    return 0
