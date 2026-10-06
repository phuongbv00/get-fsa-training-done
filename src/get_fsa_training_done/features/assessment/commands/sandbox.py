"""`get-fsa-training-done assessment sandbox` — run a testable artifact in Docker.

The rules the run is held to (no network, read-only source, bounded, removed
afterwards) are in `core/sandbox.py`, so no workflow has to remember them.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..core import sandbox


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "sandbox",
        help="run SQL scripts, unit tests or a mock API's tests in a disposable container",
        description=(
            "Prove a supplied file works, or check a submission's behaviour, without "
            "running it on this machine. The code runs with no network, from a read-only "
            "copy of --mount, under CPU, memory, process and time limits."
        ),
    )
    sub = parser.add_subparsers(dest="sandbox_command", required=True, metavar="<command>")

    check = sub.add_parser("check", help="report whether Docker is usable here")
    check.set_defaults(func=run_check)

    run = sub.add_parser(
        "run",
        help="run one command in a fresh container",
        description="Everything after -- is the command, run in a copy of --mount.",
    )
    run.add_argument("--profile", required=True, choices=list(sandbox.PROFILES))
    run.add_argument("--mount", required=True, help="directory copied into the container")
    run.add_argument(
        "--init",
        action="append",
        default=[],
        metavar="FILE",
        help="postgres: a SQL file under --mount to load before the command (repeatable)",
    )
    run.add_argument(
        "--prefetch",
        action="store_true",
        help=(
            "first fetch dependencies (maven, python, node) with the network on, running "
            "only the build tool's resolver; the command itself always runs offline"
        ),
    )
    run.add_argument("--timeout", type=int, default=sandbox.Limits.timeout, help="seconds")
    run.add_argument("--memory", default=sandbox.Limits.memory)
    run.add_argument("--cpus", default=sandbox.Limits.cpus)
    run.add_argument("argv", nargs=argparse.REMAINDER, help="-- then the command")
    run.set_defaults(func=run_command)


def run_check(args: argparse.Namespace) -> int:
    print(f"docker {sandbox.check()} — sandbox available")
    return 0


def run_command(args: argparse.Namespace) -> int:
    command = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    limits = sandbox.Limits(cpus=args.cpus, memory=args.memory, timeout=args.timeout)
    code = sandbox.run(
        args.profile,
        Path(args.mount).expanduser(),
        command,
        init=args.init,
        prefetch=args.prefetch,
        limits=limits,
    )
    print(f"sandbox: exit {code}")
    return code
