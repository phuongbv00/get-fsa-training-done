"""`gftd material verify` — is this teaching material well formed?

Structural only. Whether a note *teaches* well is a judgement the model makes;
what this checks is the shape everything downstream depends on — the title, the
section order, the numbering, the fence languages, and every link resolving.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.common.findings import Report

from ..core import checks, grammar, notes


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "verify",
        help="check lecture notes, handbooks, appendices and lab guides",
        description=(
            "Check a document, or a folder of them, against the template its "
            "filename claims. Reports the rule behind every finding."
        ),
    )
    parser.add_argument("paths", nargs="+", help="documents, or a directory of them")
    parser.add_argument(
        "--type",
        choices=tuple(grammar.BY_KEY),
        help="force a template instead of inferring it from the filename",
    )
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable")
    parser.set_defaults(func=run)


def collect(raw: list[str]) -> list[Path]:
    found: list[Path] = []
    for entry in raw:
        path = Path(entry).expanduser()
        if path.is_dir():
            found.extend(sorted(path.glob("*.md")))
        elif path.is_file():
            found.append(path)
        else:
            raise UsageError(f"not found: {path}")
    if not found:
        raise UsageError("no Markdown documents to check")
    return found


def run(args: argparse.Namespace) -> int:
    paths = collect(args.paths)
    report = Report()

    forced = grammar.BY_KEY[args.type] if args.type else None
    by_folder: dict[Path, list[Path]] = {}
    for path in paths:
        by_folder.setdefault(path.parent, []).append(path)
    for group in by_folder.values():
        # Only meaningful over a whole folder, and misleading over a subset.
        if len(group) > 1:
            checks.check_folder(group, report)

    counted: dict[str, int] = {}
    for path in paths:
        if not forced and grammar.WORKSHEET_FILENAME.match(path.name):
            counted["worksheet"] = counted.get("worksheet", 0) + 1
            continue
        template = forced or grammar.template_for(path.name)
        if template is None:
            report.error(
                "MAT-D01",
                path.name,
                "does not match any known naming convention; pass --type to check it anyway",
            )
            continue
        counted[template.key] = counted.get(template.key, 0) + 1
        checks.check(notes.parse(path), report, template=template)

    report.facts["documents"] = len(paths)
    for key, count in sorted(counted.items()):
        report.facts[key] = count

    label = f"{len(paths)} document(s)"
    if args.as_json:
        print(report.as_json(label, strict=args.strict))
        return 0 if report.ok and not (args.strict and report.warnings) else 1
    return report.report(label, strict=args.strict)
