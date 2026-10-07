"""Command-line entry point.

Lifecycle commands (`install`, `update`, `uninstall`, `status`, `doctor`,
`env`) run in whatever interpreter invoked them — they must work before any
environment exists. Every feature's worker commands (reached under
`gftd <namespace> <verb>`) re-exec into the skill's managed
virtualenv first, so they always run against the same pinned dependencies
regardless of how the CLI itself was installed.
"""

from __future__ import annotations

import argparse
import sys

from . import features
from .__about__ import CLI_NAME, SHORT_NAME, __version__
from .errors import GftdError
from .skill import SKILL

LIFECYCLE_COMMANDS = {"install", "update", "uninstall", "status", "doctor", "env"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=SHORT_NAME,
        description=(
            "Install the get-fsa-training-done agent skill in Claude Code, Codex and "
            "GitHub Copilot, and run its program, material and assessment commands."
        ),
    )
    parser.add_argument("--version", action="version", version=f"{CLI_NAME} {__version__}")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="list every affected file rather than a summary",
    )
    parser.add_argument(
        "--no-venv",
        action="store_true",
        help="run in the current interpreter instead of the managed virtualenv",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    from .lifecycle.commands import doctor, env, install, status, uninstall, update

    for module in (install, update, uninstall, status, doctor, env):
        module.add_parser(subparsers)

    features.add_parsers(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    # `update` re-runs itself after upgrading the package from PyPI.
    args.argv = argv

    if args.no_venv:
        import os

        os.environ["GET_FSA_TRAINING_DONE_NO_VENV"] = "1"

    if args.command not in LIFECYCLE_COMMANDS:
        from .lifecycle.envmgr import reexec

        reexec.enter(
            SKILL.dep_group,
            argv=argv,
            offline=bool(getattr(args, "offline", False)),
        )

    return int(args.func(args) or 0)


def run() -> None:
    """Console-script wrapper: turn our exceptions into tidy exits."""
    try:
        raise SystemExit(main())
    except GftdError as exc:
        print(f"ERROR: {exc.message}", file=sys.stderr)
        if exc.hint:
            print(f"       {exc.hint}", file=sys.stderr)
        raise SystemExit(exc.exit_code) from None
    except KeyboardInterrupt:  # pragma: no cover
        print("interrupted", file=sys.stderr)
        raise SystemExit(130) from None


if __name__ == "__main__":  # pragma: no cover
    run()
