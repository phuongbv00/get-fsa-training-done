"""`gftd update` — upgrade the CLI from PyPI, then every installed skill.

With no --platform, `update` finds every install that carries our
receipt — the shared `.agents/skills` copy, each agent's own folder and the
places earlier releases wrote to, at user and project scope — and brings them
all to this version the way `install` would lay them out today: one shared
copy, a symlink for each agent that needs one, and nothing left behind in an
old location.
"""

from __future__ import annotations

import argparse
import sys

from ...__about__ import PACKAGE_NAME, __version__
from ...errors import NotInstalledError
from ...skill import SKILL, Skill
from .. import selfupdate
from ..install import planner
from ..platforms import registry
from ..platforms.base import Platform
from . import deploy
from .common import (
    add_target_args,
    format_dest,
    project_root_of,
    validate_payload_or_die,
)


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
    name = args.name or skill.name
    if not args.check:
        validate_payload_or_die(skill.payload_dir)

    project_root = project_root_of(args)
    scopes = (registry.check_scope(args.scope),) if args.scope else ("user", "project")
    founds = deploy.discover(name, scopes, project_root)
    wanted = registry.resolve(args.platform) if args.platform else None
    if wanted is not None:
        founds = [f for f in founds if {*f.agents, *f.legacy_for} & set(wanted)]
    if not founds:
        who = ", ".join(p.label for p in wanted) if wanted else "anywhere"
        raise NotInstalledError(
            f"{skill.name} is not installed for {who}"
            if wanted
            else f"{skill.name} is not installed anywhere",
            hint="run `gftd install`",
        )

    where = ", ".join(f"{f.scope} {format_dest(f.dest)}" for f in founds)
    print(f"{skill.name}: found {len(founds)} install(s): {where}")

    if args.check:
        return 1 if any(_outdated(skill, f) for f in founds) else 0

    exit_code = 0
    for scope in scopes:
        agents: list[Platform] = []
        for found in founds:
            if found.scope != scope:
                continue
            for platform in [*found.agents, *found.legacy_for]:
                if platform not in agents and (wanted is None or platform in wanted):
                    agents.append(platform)
        if not agents:
            continue
        dep = deploy.plan(agents, scope, name, project_root, force=args.force)
        if deploy.deploy(skill, dep, args):
            exit_code = 1
    return exit_code


def _who(found: deploy.Found) -> str:
    if found.shared:
        return "shared copy"
    agents = found.agents or found.legacy_for
    return ", ".join(p.label for p in agents) or "unknown agent"


def _outdated(skill: Skill, found: deploy.Found) -> bool:
    label = f"{skill.name}: {_who(found)} ({found.scope})"
    if found.legacy_for:
        print(f"{label}: at an earlier release's location — `gftd update` moves it")
        return True
    plan = planner.build_plan(found.dest, skill.payload_dir, found.receipt, __version__)
    if found.receipt.version == __version__ and not plan.changed:
        print(f"{label}: up to date ({__version__})")
        return False
    print(f"{label}: {found.receipt.version} installed, {__version__} available")
    return True
