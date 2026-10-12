"""What a trainee is handed: the slides, the lecture note and the labs, as PDFs.

A deck's `.pptx` is the trainer's, to present from; trainees get its `.pdf`.
The PDFs are copies: the HTML stays the source, and a PDF older than it is an
export that has not been re-run.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from get_fsa_training_done.features.common.findings import Report

from . import grammar

#: The kinds a trainee is sent, as PDFs; only a deck's `.pptx` stays with the trainer.
HANDOUT_KINDS = (grammar.DECK, grammar.NOTE, grammar.LAB, grammar.WORKSHEET)
DEFAULT_FOLDER = "handout"


def documents(directory: Path) -> list[Path]:
    """The module's documents a trainee is handed, by their HTML."""
    return [
        path
        for path in sorted(directory.glob("*.html"))
        if grammar.kind_for(path.name) in HANDOUT_KINDS
    ]


def build(directory: Path, out: Path, report: Report, *, prune: bool = False) -> dict:
    """Copy each document's current PDF into `out`; report what could not be."""
    where = out.name
    out.mkdir(parents=True, exist_ok=True)
    wanted: set[str] = set()
    copied = current = 0
    for html in documents(directory):
        pdf = html.with_suffix(".pdf")
        if not pdf.is_file():
            report.error(
                "MAT-X06",
                html.name,
                f"no {pdf.name}: run `material export pdf` on it first",
            )
            continue
        if pdf.stat().st_mtime < html.stat().st_mtime:
            report.error(
                "MAT-X06",
                html.name,
                f"{pdf.name} is older than the HTML: export it again before handing it out",
            )
            continue
        wanted.add(pdf.name)
        target = out / pdf.name
        if target.is_file() and target.read_bytes() == pdf.read_bytes():
            current += 1
            continue
        shutil.copy2(pdf, target)
        copied += 1

    extra = sorted(path for path in out.iterdir() if path.name not in wanted)
    for path in extra:
        if prune and path.is_file():
            path.unlink()
            continue
        report.warn(
            "MAT-X07",
            where,
            f"{path.name} is not part of the hand-out — trainees get the slides, the lecture "
            "note and the labs as PDFs, never a .pptx; `--prune` removes it",
        )
    return {
        "hand-out files": len(wanted),
        "copied": copied,
        "already current": current,
        "not part of the hand-out": 0 if prune else len(extra),
        "pruned": len(extra) if prune else 0,
    }


__all__ = ["DEFAULT_FOLDER", "HANDOUT_KINDS", "build", "documents"]
