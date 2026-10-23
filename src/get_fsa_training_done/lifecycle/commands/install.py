"""`gftd install` — put the skill where each chosen agent looks for it.

One real copy goes to `.agents/skills`; agents that do not read that folder
get a symlink to it (see `deploy`). `--cloud` installs into the project for
every agent and wires the skill's setup script into the cloud agents' setup
steps (see `cloud`).
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ...__about__ import __version__
from ...errors import Cancelled, GftdError, UsageError
from ...skill import SKILL, Skill
from .. import prompt
from ..platforms import registry
from ..platforms.base import SCOPES, universal_root
from . import cloud
from . import deploy as deploy_mod
from .common import (
    add_target_args,
    format_dest,
    project_root_of,
    short_dest,
    validate_payload_or_die,
)
from .deploy import apply_plan


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "install",
        help="install a skill into Claude Code, Codex, GitHub Copilot and/or Antigravity",
        description=(
            "Write the skill once to .agents/skills and link every other chosen agent to "
            "it. With no --platform or --scope, ask which agents and where in a terminal."
        ),
    )
    add_target_args(parser, interactive=True)
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="never ask; with no --platform/--scope, install for claude at user scope",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an unmanaged destination, or user-modified files",
    )
    parser.add_argument(
        "--cloud",
        action="store_true",
        help=(
            "install into this project for every agent and add the setup steps cloud "
            "agents run (Claude Code on the web, GitHub Copilot coding agent, Codex cloud)"
        ),
    )
    parser.add_argument(
        "--no-prewarm",
        action="store_true",
        help="skip building the managed virtualenv(s) during install",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    skill = SKILL
    validate_payload_or_die(skill.payload_dir)
    name = args.name or skill.name
    if args.cloud:
        if args.scope == "user":
            raise UsageError(
                "--cloud installs into the project: a cloud agent sees only the repository"
            )
        args.scope = "project"
        args.platform = args.platform or registry.ALL

    try:
        dep = _deployment(skill, name, args)
    except Cancelled:
        prompt.end("Installation cancelled; nothing was written")
        return 1
    failures = deploy_mod.deploy(skill, dep, args)

    if args.cloud and not failures:
        root = dep.shared.parent.parent.parent
        cloud.report(
            root, name, cloud.setup(root, name, dry_run=args.dry_run), dry_run=args.dry_run
        )

    if not args.dry_run and not failures and not args.no_prewarm:
        _prewarm(skill, args)

    return 1 if failures else 0


def _deployment(skill: Skill, name: str, args: argparse.Namespace) -> deploy_mod.Deployment:
    """Ask in a terminal when no flag says where; otherwise the flags, or claude/user."""
    project_root = project_root_of(args)
    bare = args.platform is None and args.scope is None
    if bare and not args.yes and prompt.is_interactive():
        return _choose(skill, name, args, project_root)
    platforms = registry.resolve(args.platform or "claude")
    scope = registry.check_scope(args.scope or "user")
    return deploy_mod.plan(platforms, scope, name, project_root, force=args.force)


def _choose(
    skill: Skill, name: str, args: argparse.Namespace, project_root: Path | None
) -> deploy_mod.Deployment:
    """The `npx skills add`-style flow: agents, scope, the summary, then yes/no."""
    platforms = registry.resolve(registry.ALL)

    prompt.step(f"Skill: {skill.name} {__version__}", gap=True)
    chosen = prompt.multiselect(
        "Which agents do you want to install to?",
        [(p.label, format_dest(p.root("user"))) for p in platforms],
        empty="Select at least one agent",
    )
    picked = [platforms[i] for i in chosen]

    options = [
        ("Global", short_dest(universal_root("user"), "user")),
        ("Project", short_dest(universal_root("project", project_root), "project")),
    ]
    scope = SCOPES[prompt.select("Installation scope", options, 0)]

    dep = deploy_mod.plan(picked, scope, name, project_root, force=args.force)
    title = "Installation Summary" + (" (dry run)" if args.dry_run else "")
    prompt.box(title, deploy_mod.summary(dep))
    if not prompt.confirm("Proceed with installation?"):
        raise Cancelled("declined")
    prompt.end()
    return dep


def _prewarm(skill: Skill, args: argparse.Namespace) -> None:
    """Build the skill's venv now, so an offline machine stays self-sufficient
    later."""
    from ..envmgr import bootstrap

    try:
        bootstrap.ensure(skill.dep_group, offline=args.offline)
    except GftdError as exc:
        print(f"WARNING: could not pre-build the {skill.dep_group!r} environment: {exc.message}")


def uninstall_tree(dest: Path) -> None:  # pragma: no cover - used by tests/cleanup
    shutil.rmtree(dest, ignore_errors=True)


__all__ = ["add_parser", "apply_plan", "run"]
