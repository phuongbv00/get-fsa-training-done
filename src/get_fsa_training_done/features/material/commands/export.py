"""`gftd material export` — derive a .pptx or a .pdf from the HTML.

The HTML is the source; these files are outputs, rebuilt whenever it changes and
never edited by hand. A deck exports to the FSA template as `.pptx` (its own
layouts, so trainers can present and QA can file it) and to a 16:9 `.pdf`; a
lecture note or a lab exports to an A4 `.pdf`.

Export verifies first and refuses a document with errors: a file handed out is
harder to correct than the HTML it came from.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.features.common.findings import Report

from ..core import checks, dom, grammar


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "export",
        help="export a deck to .pptx/.pdf, or a document to .pdf",
        description="Derive a PowerPoint or PDF file from HTML material.",
    )
    sub = parser.add_subparsers(dest="export_format", required=True, metavar="<format>")
    for name, helptext in (
        ("pptx", "a deck, into the FSA template"),
        ("pdf", "a deck (16:9), or a lecture note, lab or worksheet (A4)"),
    ):
        command = sub.add_parser(name, help=helptext, description=f"Export {helptext}.")
        command.add_argument("input", help="the HTML file")
        command.add_argument("-o", "--out", help="output file (default: alongside the input)")
        command.add_argument(
            "--force", action="store_true", help="export even if verify reports errors"
        )
        command.set_defaults(func=run, export_format=name)


def run(args: argparse.Namespace) -> int:
    source = Path(args.input).expanduser()
    if not source.is_file():
        raise UsageError(f"input not found: {source}")
    kind = grammar.kind_for(source.name)
    if kind is None:
        raise UsageError(f"{source.name} is not named like a deck, lecture note, lab or worksheet")
    if args.export_format == "pptx" and kind is not grammar.DECK:
        raise UsageError(f"{source.name} is a {kind.key}; only a deck exports to .pptx")

    document = dom.parse(source)
    report = Report()
    checks.check(document, kind, report, export=True)
    for finding in report.findings:
        print(f"{finding.severity.upper()}: {finding.line()}")
    if report.errors and not args.force:
        print(f"FAIL: {source.name} has {len(report.errors)} error(s); fix them or pass --force")
        return 1

    suffix = ".pptx" if args.export_format == "pptx" else ".pdf"
    stem = source.name.removesuffix(".html")
    out = Path(args.out).expanduser() if args.out else source.with_name(stem + suffix)

    if args.export_format == "pptx":
        from ..core import export_pptx

        outcome = export_pptx.export(document, out)
        for where, message in outcome.warnings:
            print(f"WARNING: {source.name}: {where}: {message}")
        print(f"PASS: wrote {out} ({outcome.slides} slides)")
        return 0

    from ..core import export_pdf

    if kind is grammar.DECK:
        outcome = export_pdf.export_deck(document, out)
    else:
        outcome = export_pdf.export_document(document, out)
    for rule, where, message in outcome.warnings:
        print(f"WARNING: [{rule}] {source.name}: {where}: {message}")
    print(f"PASS: wrote {out} ({outcome.pages} page{'s' if outcome.pages != 1 else ''})")
    return 0
