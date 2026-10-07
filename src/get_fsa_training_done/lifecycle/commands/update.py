"""`gftd update` — upgrade the CLI from PyPI, then every installed skill.

With no --platform or --dir, `update` finds every install that carries our
receipt — each host, user and project scope — and upgrades them all, so a
user who installed into Claude and Copilot gets both refreshed in one go.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ...__about__ import PACKAGE_NAME, __version__
from ...errors import GftdError, NotInstalledError
from ...skill import SKILL, Skill
from .. import selfupdate
from ..install import migrations, planner
from ..install import receipt as receipt_mod
from ..platforms import registry
from ..platforms.base import Platform
from .common import (
    Target,
    add_target_args,
    format_dest,
    print_plan,
    project_root_of,
    resolve_targets,
    validate_payload_or_die,
)
from .install import _file_records, _report_conflicts, _venv_hint, apply_plan


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "update",
        help="upgrade the CLI from PyPI, then the installed skill",
        description=(
            "Upgrade get-fsa-training-done itself to the latest PyPI release, then "
            "compare the installed files against its payload and apply the "
            "difference. Files you edited are never overwritten without --force."
        ),
    )
    add_target_args(parser)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report whether an update is available and exit 1 if so; write nothing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite files you have modified (previous bytes kept as *.bak)",
    )
    parser.add_argument(
        "--no-self-update",
        action="store_true",
        help="skip the PyPI check and update from the package already installed",
    )
    # No --platform/--scope means "wherever it is installed", not "claude, user".
    parser.set_defaults(func=run, platform=None, scope=None)


def run(args: argparse.Namespace) -> int:
    newer = None
    if not (args.no_self_update or args.offline or selfupdate.disabled()):
        newer = _check_pypi(args)
        if newer and not args.check and not args.dry_run:
            selfupdate.upgrade(selfupdate.install_kind(), newer)
            return selfupdate.rerun(getattr(args, "argv", None) or sys.argv[1:])
    code = _run_skill(args)
    # --check: a newer package on PyPI is an available update too.
    return max(code, 1) if newer and args.check else code


def _check_pypi(args: argparse.Namespace) -> str | None:
    """The PyPI version to upgrade to, or None to stay on this one."""
    latest = selfupdate.latest_version()
    if latest is None:
        print(f"{PACKAGE_NAME}: could not reach PyPI; updating from {__version__}")
        return None
    if not selfupdate.is_newer(latest):
        return None
    kind = selfupdate.install_kind()
    if kind in ("editable", "source"):
        print(
            f"{PACKAGE_NAME}: {latest} is on PyPI, but this is a {kind} checkout "
            f"at {__version__} — pull it to upgrade"
        )
        return None
    if args.check or args.dry_run:
        print(f"{PACKAGE_NAME}: {__version__} installed, {latest} on PyPI")
    return latest


def _run_skill(args: argparse.Namespace) -> int:
    skill = SKILL
    exit_code = 0

    payload = skill.payload_dir
    if not args.check:
        validate_payload_or_die(payload)

    if args.platform is None and not args.dir:
        targets = installed_targets(skill, args)
        if not targets:
            raise NotInstalledError(
                f"{skill.name} is not installed anywhere",
                hint="run `gftd install --platform all`",
            )
    else:
        args.platform = args.platform or "claude"
        args.scope = args.scope or "user"
        targets = resolve_targets(args, skill)

    for platform, scope, dest in targets:
        try:
            outdated = _update_one(skill, platform, scope, dest, args, payload)
            if args.check and outdated:
                exit_code = 1
        except GftdError as exc:
            exit_code = max(exit_code, exc.exit_code)
            print(f"ERROR: {skill.name}: {platform.label} ({scope}): {exc.message}")
            if exc.hint:
                print(f"       {exc.hint}")
    return exit_code


def installed_targets(skill: Skill, args: argparse.Namespace) -> list[Target]:
    """Every destination holding our receipt, across hosts and scopes."""
    name = args.name or skill.name
    project_root = project_root_of(args)
    scopes = (args.scope,) if args.scope else ("user", "project")
    targets: list[Target] = []
    seen: set[Path] = set()
    for platform in registry.resolve(registry.ALL):
        for scope in scopes:
            if scope == "project" and not platform.project_subdir:
                continue
            dest = platform.dest(scope, name, project_root)
            # From the home directory, project scope is the user-scope folder.
            if dest.resolve() in seen or receipt_mod.read(dest) is None:
                continue
            seen.add(dest.resolve())
            targets.append((platform, scope, dest))
    if targets:
        where = ", ".join(f"{p.label} ({s}) {format_dest(d)}" for p, s, d in targets)
        print(f"{skill.name}: found {len(targets)} install(s): {where}")
    return targets


def _update_one(
    skill: Skill,
    platform: Platform,
    scope: str,
    dest: Path,
    args: argparse.Namespace,
    payload: Path,
) -> bool:
    label = f"{skill.name}: {platform.label} ({scope})"
    existing = receipt_mod.read(dest)
    if existing is None:
        raise NotInstalledError(
            f"{dest} is not managed by get-fsa-training-done",
            hint="run `gftd install` (add --force to adopt an existing directory)",
        )

    plan = planner.build_plan(dest, payload, existing, __version__)
    same_version = existing.version == __version__

    if args.check:
        if same_version and not plan.changed:
            print(f"{label}: up to date ({__version__})")
            return False
        print(f"{label}: {existing.version} installed, {__version__} available")
        return True

    if same_version and not plan.changed and not args.force:
        print(f"{label}: already at {__version__} — {dest}")
        return False

    if args.dry_run:
        print(f"{label}: would update {existing.version} -> {__version__} at {dest}")
        print_plan(plan, verbose=args.verbose)
        return True

    apply_plan(dest, payload, plan, force=args.force)

    notes = migrations.run_all(dest, existing.version)

    receipt_mod.write(
        dest,
        receipt_mod.Receipt(
            version=__version__,
            skill_name=existing.skill_name or skill.name,
            platform=platform.key,
            scope=scope,
            dest=str(dest),
            installed_at=receipt_mod.utc_now(),
            installed_by=receipt_mod.installed_by(),
            cli=receipt_mod.cli_invocation(),
            dirs=plan.dirs,
            files=_file_records(dest, plan, force=args.force),
            venv=existing.venv or str(_venv_hint(skill)),
        ),
    )

    print(f"{label}: updated {existing.version} -> {__version__} at {dest}")
    print_plan(plan, verbose=args.verbose)
    for note in notes:
        print(f"  migration: {note}")
    _report_conflicts(plan, force=args.force)
    return True
