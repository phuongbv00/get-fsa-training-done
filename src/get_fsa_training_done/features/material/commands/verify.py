"""`gftd material verify` — is this teaching material well formed?

Checks each document against the shape its filename claims: a deck against the
FSA template's layouts and order, a note or lab against its parts and the
learning rules (objectives traced to questions, answers present, something to
try after each idea). Whether a document *teaches* well is still a judgement the
model makes; these are the parts of that judgement that can be counted.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.common.findings import Report

from ..core import checks, dom, grammar


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "verify",
        help="check slide decks, lecture notes, labs and worksheets",
        description=(
            "Check a document, or a folder of them, against the shape its "
            "filename claims. Reports the rule behind every finding."
        ),
    )
    parser.add_argument("paths", nargs="+", help="documents, or a directory of them")
    parser.add_argument(
        "--type",
        choices=tuple(grammar.KIND_BY_KEY),
        help="force a kind instead of inferring it from the filename",
    )
    parser.add_argument(
        "--minutes-per-slide",
        default="{:g}-{:g}".format(*checks.MINUTES_PER_SLIDE),
        help="the range a deck's slide count is checked against (default: %(default)s)",
    )
    parser.add_argument(
        "--min-fit",
        type=float,
        default=checks.MIN_FIT,
        help="report a title or text slot shrunk below this share of its size "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="also apply the rules that only matter for a .pptx or .pdf (MAT-X*)",
    )
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable")
    parser.set_defaults(func=run)


def collect(raw: list[str]) -> list[Path]:
    found: list[Path] = []
    for entry in raw:
        path = Path(entry).expanduser()
        if path.is_dir():
            found.extend(sorted(path.glob("*.html")))
        elif path.is_file():
            found.append(path)
        else:
            raise UsageError(f"not found: {path}")
    if not found:
        raise UsageError("no HTML documents to check")
    return found


def parse_range(text: str) -> tuple[float, float]:
    try:
        low, high = (float(part) for part in text.split("-", 1))
    except ValueError as exc:
        raise UsageError(f"--minutes-per-slide takes a range such as 1.5-6, not {text!r}") from exc
    if not 0 < low <= high:
        raise UsageError(f"--minutes-per-slide needs 0 < low <= high, not {text!r}")
    return low, high


def run(args: argparse.Namespace) -> int:
    paths = collect(args.paths)
    report = Report()
    minutes_per_slide = parse_range(args.minutes_per_slide)

    by_folder: dict[Path, list[Path]] = {}
    for path in paths:
        by_folder.setdefault(path.parent, []).append(path)
    for group in by_folder.values():
        # Only meaningful over a whole folder, and misleading over a subset.
        if len(group) > 1:
            checks.check_folder(group, report)

    counted: dict[str, int] = {}
    for path in paths:
        key = _check(path, args, report, minutes_per_slide)
        if key:
            counted[key] = counted.get(key, 0) + 1

    report.facts["documents"] = len(paths)
    for key, count in sorted(counted.items()):
        report.facts[key] = count

    label = f"{len(paths)} document(s)"
    if args.as_json:
        print(report.as_json(label, strict=args.strict))
        return 0 if report.ok and not (args.strict and report.warnings) else 1
    return report.report(label, strict=args.strict)


def _check(path: Path, args: argparse.Namespace, report: Report, minutes_per_slide) -> str | None:
    kind = grammar.KIND_BY_KEY.get(args.type) if args.type else grammar.kind_for(path.name)
    if kind is None:
        message = grammar.legacy(path.name) or (
            "does not match any known naming convention; pass --type to check it anyway"
        )
        report.error("MAT-D01", path.name, message)
        return None
    checks.check(
        dom.parse(path),
        kind,
        report,
        export=args.export,
        minutes_per_slide=minutes_per_slide,
        min_fit=args.min_fit,
    )
    return kind.key
