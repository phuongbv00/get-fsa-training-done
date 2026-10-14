"""Shared argument wiring and output helpers for the lifecycle commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...errors import GftdError
from ..install.planner import ACTION_ORDER, Action, Plan
from ..platforms import registry
from ..platforms.base import Platform

_WARNED_SCOPES: set[tuple[str, str]] = set()


def add_verbose(parser: argparse.ArgumentParser) -> None:
    """Accept `-v` after the subcommand as well as before it.

    `argparse.SUPPRESS` keeps the subparser from clobbering a `-v` that was
    given globally: the attribute is only set when the flag actually appears.
    """
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=argparse.SUPPRESS,
        help="list every affected file rather than a summary",
    )


def add_target_args(parser: argparse.ArgumentParser, *, interactive: bool = False) -> None:
    """The flags that say where a skill goes.

    With `interactive`, `--platform` and `--scope` default to None so the
    command can tell "no flags given" apart from "claude, user" and ask in a
    terminal instead; it fills in the old defaults itself when nobody is there.
    There is no `--dir`: the skill only ever goes to the shared `.agents/skills`
    copy and the agents' own folders, never a folder of the user's choosing,
    so `update` and `uninstall` can always find it.
    """
    add_verbose(parser)
    default = "ask in a terminal, else claude" if interactive else "claude"
    parser.add_argument(
        "--platform",
        default=None if interactive else "claude",
        help=f"target host: {', '.join(registry.names())}, or 'all' (default: {default})",
    )
    default = "ask in a terminal, else user" if interactive else "user"
    parser.add_argument(
        "--scope",
        default=None if interactive else "user",
        choices=("user", "project"),
        help=f"install for the whole account (user) or just this project (default: {default})",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="override the installed directory name",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="project root for --scope project (default: the current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would change without touching anything",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="never reach the network; fail instead",
    )


def project_root_of(args: argparse.Namespace) -> Path | None:
    raw = getattr(args, "project_root", None)
    return Path(raw).expanduser().resolve() if raw else None


def warn_unverified_scope(platform: Platform, scope: str) -> None:
    """Say so plainly when we are writing somewhere we have not confirmed works."""
    if scope != "project" or platform.project_scope_verified:
        return
    key = (platform.key, scope)
    if key in _WARNED_SCOPES:
        return
    _WARNED_SCOPES.add(key)
    print(
        f"WARNING: project-scope discovery is unconfirmed for {platform.label}; "
        "the files will be written but the host may not pick them up"
    )


def validate_payload_or_die(payload_dir: Path) -> None:
    """Apply the strictest host's rules to the payload, whatever the target.

    One payload has to satisfy every host we support, so a Claude-only install
    still gets checked against Codex's rules. Failing here is much cheaper than
    a skill that silently never loads.
    """
    problems = registry.get("codex").validate(payload_dir)
    fatal = [p for p in problems if p.fatal]
    for problem in problems:
        print(problem)
    if fatal:
        raise GftdError(
            f"the bundled skill payload is invalid ({len(fatal)} error(s))",
            hint="this is a packaging bug; please report it",
        )


def print_plan(plan: Plan, *, verbose: bool = False) -> None:
    if not plan.changed and not verbose:
        return
    print(f"  {plan.summary()}")
    if not verbose:
        return
    for action in ACTION_ORDER:
        entries = plan.by_action(action)
        if not entries or action is Action.KEEP:
            continue
        for entry in entries:
            print(f"    {action.value:<8} {entry.path}")


def format_dest(dest: Path) -> str:
    try:
        return "~/" + str(dest.relative_to(Path.home()))
    except ValueError:
        return str(dest)


def short_dest(dest: Path, scope: str) -> str:
    """A project path relative to the working directory, anything else `~/...`."""
    if scope == "project":
        try:
            return "./" + dest.relative_to(Path.cwd()).as_posix()
        except ValueError:
            pass
    return format_dest(dest)
