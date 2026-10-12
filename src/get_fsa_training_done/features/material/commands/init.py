"""`gftd material init` — put the FSA theme beside a module's material.

Every page links `_theme/fsa.css` (and a deck `_theme/deck.js`) by a relative
path, so a module folder opens correctly in any browser, from a file share or a
zip, with nothing installed. This copies the theme there, and refreshes it when
the skill's theme changes.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from get_fsa_training_done.errors import UsageError

from ..core import grammar

THEME = Path(__file__).resolve().parents[1] / "theme"
#: Only the exporter reads the template; a browser never needs it.
SKIP = ("fsa_base.pptx",)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "init",
        help="copy the FSA theme into a module's material folder",
        description=(
            f"Create or refresh <dir>/{grammar.THEME_DIR}/: the stylesheet, the deck "
            "viewer and the template's backgrounds every page links to."
        ),
    )
    parser.add_argument("--dir", required=True, dest="directory", help="the materials folder")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    directory = Path(args.directory).expanduser()
    if directory.exists() and not directory.is_dir():
        raise UsageError(f"not a directory: {directory}")
    target = directory / grammar.THEME_DIR
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(THEME, target, ignore=shutil.ignore_patterns(*SKIP))
    files = sum(1 for path in target.rglob("*") if path.is_file())
    print(f"PASS: wrote {target} ({files} files)")
    return 0
