"""`gftd material derive` — compute the lecture note's syllabus map.

The map is a transcription of the topic outline with a link to the topic of the
note that covers each item. Its anchors break when a heading is renamed and
nothing else notices — which is exactly the case for deriving it rather than
maintaining it.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from ..core import dom
from ..core import syllabus_map as map_mod


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "derive",
        help="compute what can be derived from the syllabus and the note",
        description="Derive the lecture note's syllabus map from the outline and its topics.",
    )
    sub = parser.add_subparsers(dest="derive_target", required=True, metavar="<target>")

    syllabus_map = sub.add_parser(
        "syllabus-map",
        help="the lecture note's syllabus map",
        description=(
            "Match each topic-outline item to the note's topic that covers it and "
            "emit the map. Printed by default; --write patches the note."
        ),
    )
    syllabus_map.add_argument("--syllabus", required=True, help="the topic syllabus")
    syllabus_map.add_argument("--note", required=True, help="the module's lecture note")
    mode = syllabus_map.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="patch the note in place")
    mode.add_argument("--check", action="store_true", help="exit 1 if the map is stale")
    syllabus_map.set_defaults(func=run_syllabus_map)


def run_syllabus_map(args: argparse.Namespace) -> int:
    syllabus = Path(args.syllabus).expanduser()
    if not syllabus.is_file():
        raise UsageError(f"syllabus not found: {syllabus}")
    path = Path(args.note).expanduser()
    if not path.is_file():
        raise UsageError(f"lecture note not found: {path}")
    # The map is written in the note's own language (`<html lang>`).
    body = map_mod.render(syllabus.read_text(encoding="utf-8"), dom.parse(path))
    if not (args.write or args.check):
        print(body)
        return 0

    original = path.read_text(encoding="utf-8")
    updated = map_mod.patch(original, body)

    if args.check:
        if updated != original:
            print(f"FAIL: {path.name}'s syllabus map is out of date")
            print(body)
            return 1
        print(f"PASS: {path.name}'s syllabus map is current")
        return 0

    if updated == original:
        print(f"PASS: {path.name}'s syllabus map is already current")
        return 0
    path.write_text(updated, encoding="utf-8")
    print(f"PASS: rewrote the syllabus map in {path.name}")
    return 0
