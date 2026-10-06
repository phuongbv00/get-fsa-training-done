"""`gftd assessment render` — export a learner brief to a print-ready PDF.

Only briefs. Rubrics are instructor-only and must never be handed out as a PDF
alongside the brief, so this command refuses one unless explicitly overridden.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from get_fsa_training_done.errors import GftdError, UsageError

from ..core import budget as budget_mod
from ..core import html as html_mod
from ..core import markdown as md
from ..core import pdf as pdf_mod


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "render",
        help="export a Markdown brief to a print-ready A4 PDF",
        description=(
            "Render a learner brief to A4 PDF and check it against its page budget. "
            "The budget comes from the brief's Duration header at two pages per hour."
        ),
    )
    parser.add_argument("input", help="path to the Markdown brief")
    parser.add_argument("-o", "--out", help="output PDF (default: alongside the input)")
    parser.add_argument(
        "--max-pages",
        type=int,
        help="page budget override; by default it is derived from the Duration header",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="document language attribute (default: en; pass vi for a translated brief)",
    )
    parser.add_argument(
        "--allow-rubric",
        action="store_true",
        help="render a file whose name marks it as an instructor rubric",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    source = Path(args.input).expanduser()
    if not source.is_file():
        raise UsageError(f"input not found: {source}")

    if "_rubric" in source.stem and not args.allow_rubric:
        raise UsageError(
            f"{source.name} looks like an instructor rubric",
            hint=(
                "rubrics are instructor-only and should not be handed out as a PDF; "
                "pass --allow-rubric if you really mean to render it"
            ),
        )

    out_pdf = Path(args.out).expanduser() if args.out else source.with_suffix(".pdf")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    markdown = source.read_text(encoding="utf-8")
    title = md.document_title(markdown, source.stem)
    document = html_mod.build_document(markdown, title, lang=args.lang)

    pages = pdf_mod.render_html(document, out_pdf)
    size_kb = out_pdf.stat().st_size / 1024
    page_note = f", {pages} page{'s' if pages != 1 else ''}" if pages else ""
    print(f"PASS: wrote {out_pdf} ({size_kb:.0f} KB{page_note})")

    limit, source_label = budget_mod.page_budget_for(markdown, override=args.max_pages)
    if limit is None:
        print(f"NOTE: no page budget enforced — {source_label}")
        return 0
    if pages is None:
        print("WARNING: could not determine the page count; budget not enforced")
        return 0
    if pages > limit:
        raise GftdError(
            f"brief is {pages} A4 pages but the budget is {limit} (from {source_label})",
            hint=(
                "cut content — restated context, paragraphs that could be bullets, "
                "anything the rubric already covers. Re-rendering will not fix it."
            ),
        )
    print(f"PASS: {pages}/{limit} A4 pages (budget from {source_label})")
    return 0
