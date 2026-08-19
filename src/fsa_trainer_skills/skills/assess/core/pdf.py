"""Driving headless Chrome to print a brief, and counting the pages it made.

Chrome's print engine is the renderer because the existing brief PDFs were
produced that way and must keep matching. It runs entirely offline: the page we
hand it is a single self-contained file with inline CSS and no remote assets.

Page counting reads the PDF bytes directly rather than pulling in a PDF library.
The page budget is the one check that cannot be done by reading the Markdown, so
it has to work everywhere the renderer works.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from fsa_trainer_skills.errors import MissingToolError

#: macOS application bundles, tried before anything on PATH.
MAC_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
)
PATH_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
    "brave-browser",
)

_PAGE_OBJECT = re.compile(rb"/Type\s*/Page(?![s])")
_PAGE_COUNT = re.compile(rb"/Count\s+(\d+)")

RENDER_DEADLINE_SECONDS = 60


def find_chrome(explicit: str | None = None) -> str:
    """First usable browser binary, or "" when there is none."""
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("CHROME_BIN"):
        candidates.append(os.environ["CHROME_BIN"])
    candidates.extend(MAC_CANDIDATES)
    for name in PATH_CANDIDATES:
        found = shutil.which(name)
        if found:
            candidates.append(found)

    for candidate in candidates:
        if candidate and os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
        resolved = shutil.which(candidate) if candidate else None
        if resolved:
            return resolved
    return ""


def require_chrome(explicit: str | None = None) -> str:
    chrome = find_chrome(explicit)
    if not chrome:
        raise MissingToolError(
            "no Chrome, Chromium, or Edge binary found",
            hint="install one, pass --chrome PATH, or set CHROME_BIN",
        )
    return chrome


def render(chrome: str, html_path: Path, out_pdf: Path) -> None:
    """Print `html_path` to `out_pdf`.

    New headless writes the PDF reliably but does not always exit on its own, so
    we watch for the output file to stop growing and then stop Chrome ourselves
    instead of waiting on the process. Legacy `--headless` is the fallback for
    older builds.
    """
    profile = Path(tempfile.mkdtemp(prefix="fsa-trainer-skills-chrome-"))
    common = [
        "--disable-gpu",
        "--no-sandbox",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile}",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out_pdf}",
        "--virtual-time-budget=5000",
        html_path.as_uri(),
    ]

    out_pdf.unlink(missing_ok=True)
    last_error = ""
    try:
        for headless in (["--headless=new"], ["--headless"]):
            process = subprocess.Popen(
                [chrome, *headless, *common],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                if _wait_for_output(process, out_pdf):
                    return
                if process.stderr:
                    last_error = process.stderr.read().decode(errors="replace").strip()
            finally:
                _terminate(process)
            out_pdf.unlink(missing_ok=True)

        raise MissingToolError(
            "Chrome ran but produced no PDF",
            hint=last_error.splitlines()[-1] if last_error else None,
        )
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def _wait_for_output(process: subprocess.Popen, out_pdf: Path) -> bool:
    """True once the PDF exists and its size has stopped changing."""
    deadline = time.monotonic() + RENDER_DEADLINE_SECONDS
    previous = -1
    while time.monotonic() < deadline:
        exited = process.poll() is not None
        size = out_pdf.stat().st_size if out_pdf.exists() else 0
        if size > 0 and size == previous:
            return True
        previous = size
        if exited:
            return out_pdf.exists() and out_pdf.stat().st_size > 0
        time.sleep(0.5)
    return out_pdf.exists() and out_pdf.stat().st_size > 0


def _terminate(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover
            process.kill()


def count_pages(pdf: Path) -> int | None:
    """Page count from the raw PDF, or None if it cannot be determined.

    Two independent signals: `/Type /Page` objects and the page tree's `/Count`.
    They normally agree; taking the larger means a compressed page tree can
    never under-report and let an over-long brief slip past the budget.
    """
    try:
        raw = pdf.read_bytes()
    except OSError:
        return None
    by_object = len(_PAGE_OBJECT.findall(raw))
    counts = [int(value) for value in _PAGE_COUNT.findall(raw)]
    best = max(by_object, max(counts) if counts else 0)
    return best or None
