"""`get-fsa-training-done material derive` — compute the appendix's syllabus map.

The map is a transcription of the topic outline with a link into the note that
covers each item. Its deep anchors are the only ones in the corpus, so a renamed
heading breaks them and nothing else notices — which is exactly the case for
deriving it rather than maintaining it.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from ..core import appendix as appendix_mod


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "derive",
        help="compute what can be derived from the syllabus and the notes",
        description="Derive the appendix's syllabus map from the outline and the notes.",
    )
    sub = parser.add_subparsers(dest="derive_target", required=True, metavar="<target>")

    appendix = sub.add_parser(
        "appendix",
        help="the appendix's syllabus map",
        description=(
            "Match each topic-outline item to the note that covers it and emit "
            "the map. Printed by default; --write patches the appendix."
        ),
    )
    appendix.add_argument("--syllabus", required=True, help="the topic syllabus")
    appendix.add_argument("--dir", required=True, dest="directory", help="the materials folder")
    appendix.add_argument("--appendix", help="the appendix to patch or check")
    mode = appendix.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="patch the appendix in place")
    mode.add_argument("--check", action="store_true", help="exit 1 if the map is stale")
    appendix.set_defaults(func=run_appendix)


def run_appendix(args: argparse.Namespace) -> int:
    syllabus = Path(args.syllabus).expanduser()
    if not syllabus.is_file():
        raise UsageError(f"syllabus not found: {syllabus}")
    directory = Path(args.directory).expanduser()
    body = appendix_mod.render(syllabus.read_text(encoding="utf-8"), directory)

    if (args.write or args.check) and not args.appendix:
        raise UsageError("--write and --check need --appendix")
    if not args.appendix:
        print(body)
        return 0

    path = Path(args.appendix).expanduser()
    if not path.is_file():
        raise UsageError(f"appendix not found: {path}")
    original = path.read_text(encoding="utf-8")
    updated = appendix_mod.patch(original, body)

    if args.check:
        if updated != original:
            print(f"FAIL: {path.name}'s syllabus map is out of date")
            print(body)
            return 1
        print(f"PASS: {path.name}'s syllabus map is current")
        return 0

    if args.write:
        if updated == original:
            print(f"PASS: {path.name}'s syllabus map is already current")
            return 0
        path.write_text(updated, encoding="utf-8")
        print(f"PASS: rewrote the syllabus map in {path.name}")
        return 0

    print(body)
    return 0
