"""`gftd uninstall` — remove exactly what was written, and nothing else.

Uninstall is all or nothing: every install is found — the shared
`.agents/skills` copy at user and project scope, the symlinks into it, each
agent's own copy and what an earlier release left behind — shown in one
summary, and removed on a single yes. There is no removing it from one agent:
the agents share one copy, so taking it from one would take it from all.
Without a terminal to ask in, `--yes` is the answer.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ...errors import Cancelled, GftdError
from ...skill import SKILL, Skill
from .. import prompt
from ..install import links, removal
from ..install import receipt as receipt_mod
from ..platforms.base import Platform
from . import deploy
from .common import add_verbose, format_dest, project_root_of, short_dest

#: How many kept files the summary names before it says `+N more`.
KEPT_SHOWN = 3


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "uninstall",
        help="remove the skill from every agent",
        description=(
            "Find every install — the shared .agents/skills copy, the links into it and "
            "any earlier install — show what would go, and remove all of it on one yes. "
            "Files you added or edited are left in place unless --force is given."
        ),
    )
    add_verbose(parser)
    parser.add_argument("--name", default=None, help="override the installed directory name")
    parser.add_argument(
        "--project-root",
        default=None,
        help="project whose install to remove as well (default: the current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would be removed without touching anything",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="remove without asking; required when there is no terminal to ask in",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="remove whole directories, including files get-fsa-training-done did not write",
    )
    parser.add_argument(
        "--purge-venv",
        action="store_true",
        help="also delete the managed virtualenvs",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    skill = SKILL
    outcome = _uninstall_everything(skill, args)
    if outcome is None:
        return 0 if args.dry_run else 1
    removed_any, failures = outcome

    if args.purge_venv and removed_any and not args.dry_run:
        from ..envmgr import bootstrap

        for path in bootstrap.purge():
            print(f"removed environment {path}")

    return 1 if failures else 0


def _report(skill: Skill, who: str, scope: str, exc: GftdError) -> None:
    print(f"ERROR: {skill.name}: {who} ({scope}): {exc.message}")
    if exc.hint:
        print(f"       {exc.hint}")


# ------------------------------------------------------------------- everything


def _uninstall_everything(skill: Skill, args: argparse.Namespace) -> tuple[bool, int] | None:
    """Every install, shown in one summary; all of them on yes, none on no.

    Returns None when nothing was removed on purpose: a dry run, or a no.
    """
    name = args.name or skill.name
    founds = deploy.discover(name, ("user", "project"), project_root_of(args))
    if not founds:
        print(f"{skill.name} is not installed anywhere")
        return None if args.dry_run else (False, 0)

    title = "Uninstall Summary" + (" (dry run)" if args.dry_run else "")
    prompt.box(title, summary(founds, args))
    if args.dry_run:
        prompt.end("dry run; nothing was removed")
        return None
    if not args.yes:
        if not prompt.is_interactive():
            prompt.end("nothing was removed: pass --yes to remove without asking")
            return None
        try:
            agreed = prompt.confirm("Proceed with uninstall?", default=False)
        except Cancelled:
            agreed = False
        if not agreed:
            prompt.end("Uninstall cancelled; nothing was removed")
            return None
    prompt.end()

    failures = 0
    for found in founds:
        try:
            who = "shared copy" if found.shared else _who(found)
            _remove(skill, who, found.scope, found.dest, found.receipt, args, found.links)
        except GftdError as exc:
            failures += 1
            _report(skill, _who(found), found.scope, exc)
    return True, failures


def summary(founds: list[deploy.Found], args: argparse.Namespace) -> list[str]:
    """The lines of the "Uninstall Summary" box."""
    paint = prompt.paint
    lines: list[str] = []
    for found in founds:
        if lines:
            lines.append("")
        lines.append(paint(short_dest(found.dest, found.scope), "36"))
        linked = {p for p, _ in found.links if p is not None}
        direct = [p for p in found.agents if p not in linked]
        if direct:
            label = "universal:" if found.shared else "agent:"
            names = prompt.selected_summary([p.label for p in direct])
            lines.append(f"  {paint(label, '32')} {names}")
        if found.links:
            owners = [p.label if p else format_dest(path) for p, path in found.links]
            lines.append(f"  symlink → {prompt.selected_summary(owners)}")
        if found.legacy_for:
            names = ", ".join(p.label for p in found.legacy_for)
            lines.append(paint(f"  where an earlier release installed for {names}", "2"))
        if args.force:
            lines.append(f"  {paint('removes:', '31')} the whole folder")
            continue
        to_delete, _ = removal.classify_recorded(found.dest, found.receipt)
        lines.append(f"  {paint('removes:', '31')} {len(to_delete)} files")
        kept = deploy._user_files(found.dest, found.receipt)
        if kept:
            shown = ", ".join(kept[:KEPT_SHOWN])
            more = f" +{len(kept) - KEPT_SHOWN} more" if len(kept) > KEPT_SHOWN else ""
            lines.append(f"  {paint('keeps:', '33')} {shown}{more} (edited or added by you)")
    if args.purge_venv:
        for venv in _venvs():
            lines.append("")
            lines.append(paint(format_dest(venv), "36"))
            lines.append(f"  {paint('removes:', '31')} the managed virtualenv")
    return lines


def _who(found: deploy.Found) -> str:
    agents = found.agents or found.legacy_for
    return ", ".join(p.label for p in agents) or "unknown agent"


def _venvs() -> list[Path]:
    from ..envmgr import stamp

    root = stamp.home() / "venvs"
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


# ---------------------------------------------------------------------- removing


def _remove(
    skill: Skill,
    who: str,
    scope: str,
    dest: Path,
    receipt: receipt_mod.Receipt,
    args: argparse.Namespace,
    found_links: list[tuple[Platform | None, Path]],
) -> bool:
    """Delete one install and, once it is gone, the symlinks into it."""
    label = f"{skill.name}: {who} ({scope})"
    if args.dry_run:
        if args.force:
            print(f"{label}: would remove the whole directory {dest}")
        else:
            to_delete, kept = removal.classify_recorded(dest, receipt)
            print(f"{label}: would remove {len(to_delete)} file(s) from {dest}")
            if kept:
                print(f"  {len(kept)} modified file(s) would be kept")
        for owner, link in found_links:
            who = f"{skill.name}: {owner.label} ({scope})" if owner else label
            print(f"{who}: would remove the link {format_dest(link)}")
        return True

    if args.force:
        shutil.rmtree(dest, ignore_errors=True)
        leftovers: list[Path] = []
        print(f"{label}: removed {dest}")
    else:
        to_delete, leftovers = removal.remove_recorded(dest, receipt)
        if not leftovers:
            print(f"{label}: removed {dest}")
        else:
            print(f"{label}: removed {len(to_delete)} file(s); kept {len(leftovers)} in {dest}")
            for rel in leftovers[:10]:
                print(f"    kept {rel.as_posix()}")
            if len(leftovers) > 10:
                print(f"    ... and {len(leftovers) - 10} more")

    if leftovers:
        # The user's files are still there; the links keep them where they were.
        return True
    for owner, link in found_links:
        if links.remove(link):
            who = f"{skill.name}: {owner.label} ({scope})" if owner else label
            print(f"{who}: removed the link {format_dest(link)}")
    return True
