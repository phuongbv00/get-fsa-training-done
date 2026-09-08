"""Shared argument wiring and output helpers for the lifecycle commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from .. import skills as skill_registry
from ..errors import FsaTrainerSkillsError, UsageError
from ..install.planner import ACTION_ORDER, Action, Plan
from ..platforms import registry
from ..platforms.base import Platform
from ..skillkit import Skill

Target = tuple[Platform, str, Path]

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


def add_target_args(parser: argparse.ArgumentParser) -> None:
    add_verbose(parser)
    parser.add_argument(
        "--skill",
        default=skill_registry.ALL,
        help=f"skill to target: {', '.join(skill_registry.names())}, or 'all' (default: all)",
    )
    parser.add_argument(
        "--platform",
        default="claude",
        help=f"target host: {', '.join(registry.names())}, or 'all' (default: claude)",
    )
    parser.add_argument(
        "--scope",
        default="user",
        choices=("user", "project"),
        help="install for the whole account (user) or just this project (default: user)",
    )
    parser.add_argument(
        "--dir",
        dest="dir",
        default=None,
        help="explicit destination directory, overriding --platform/--scope",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="override the installed directory name (requires a single --skill)",
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


def resolve_skills(args: argparse.Namespace) -> list[Skill]:
    """Expand `--skill` into concrete `Skill` objects, gating name/dir overrides."""
    chosen = skill_registry.resolve(args.skill)
    if getattr(args, "name", None) and len(chosen) != 1:
        raise UsageError(
            "--name requires a single --skill, not 'all'",
            hint=f"pass --skill <one of: {', '.join(skill_registry.names())}>",
        )
    if getattr(args, "dir", None) and len(chosen) != 1:
        raise UsageError("--dir requires a single --skill, not 'all'")
    return chosen


def project_root_of(args: argparse.Namespace) -> Path | None:
    raw = getattr(args, "project_root", None)
    return Path(raw).expanduser().resolve() if raw else None


def clean_legacy_installs(
    skill: Skill,
    platform: Platform,
    scope: str,
    dest: Path,
    args: argparse.Namespace,
    label: str,
) -> None:
    """Clear installs left behind under a name this skill used to have.

    Renaming a skill changes its install directory, so the old one is orphaned
    — and an orphan is not inert: the host still loads it, so the agent sees two
    skills claiming the same triggers. `--dir` and `--name` are skipped because
    the caller has named an exact destination, and inferring siblings from that
    would be guessing.
    """
    if getattr(args, "dir", None) or getattr(args, "name", None):
        return
    from ..install import legacy

    for item in legacy.find(skill, platform, scope, project_root_of(args), current_dest=dest):
        for line in legacy.clean(item, dry_run=bool(getattr(args, "dry_run", False))):
            print(f"{label}: {line}")


def resolve_targets(args: argparse.Namespace, skill: Skill) -> list[Target]:
    """Expand --platform/--scope/--dir into concrete destinations for `skill`."""
    name = args.name or skill.name
    scope = registry.check_scope(args.scope)
    project_root = project_root_of(args)

    if args.dir:
        dest = Path(args.dir).expanduser().resolve()
        platforms = registry.resolve(args.platform)
        if args.platform == registry.ALL:
            raise UsageError("--dir cannot be combined with --platform all")
        return [(platforms[0], scope, dest)]

    targets: list[Target] = []
    for platform in registry.resolve(args.platform):
        if scope == "project" and not platform.project_subdir:
            print(f"SKIPPED: {platform.label} has no project scope")
            continue
        targets.append((platform, scope, platform.dest(scope, name, project_root)))
    if not targets:
        raise UsageError("no installable targets for the requested platform/scope")
    return targets


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
        raise FsaTrainerSkillsError(
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
