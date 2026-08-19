"""`fsa-trainer-skills install` — materialise a skill payload into a host."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ..__about__ import __version__
from ..errors import FsaTrainerSkillsError, UnmanagedDestinationError
from ..install import fsops, planner
from ..install import receipt as receipt_mod
from ..install.planner import Action, Plan
from ..platforms.base import Platform
from ..skillkit import Skill
from .common import (
    add_target_args,
    print_plan,
    resolve_skills,
    resolve_targets,
    validate_payload_or_die,
    warn_unverified_scope,
)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "install",
        help="install a skill into Claude Code and/or Codex",
        description="Copy a skill's bundled payload into a host's skills directory.",
    )
    add_target_args(parser)
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an unmanaged destination, or user-modified files",
    )
    parser.add_argument(
        "--no-prewarm",
        action="store_true",
        help="skip building the managed virtualenv(s) during install",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    skills = resolve_skills(args)
    failures = 0

    for skill in skills:
        validate_payload_or_die(skill.payload_dir)
        name = args.name or skill.name
        for platform, scope, dest in resolve_targets(args, skill):
            try:
                _install_one(skill, name, platform, scope, dest, args, skill.payload_dir)
            except FsaTrainerSkillsError as exc:
                failures += 1
                print(f"ERROR: {skill.name}: {platform.label} ({scope}): {exc.message}")
                if exc.hint:
                    print(f"       {exc.hint}")

    if not args.dry_run and not failures and not args.no_prewarm:
        _prewarm(skills, args)

    return 1 if failures else 0


def _install_one(
    skill: Skill,
    name: str,
    platform: Platform,
    scope: str,
    dest: Path,
    args: argparse.Namespace,
    payload: Path,
) -> None:
    warn_unverified_scope(platform, scope)

    existing = receipt_mod.read(dest)
    if existing is None and dest.exists() and any(dest.iterdir()):
        if not args.force:
            raise UnmanagedDestinationError(
                f"{dest} already exists and was not installed by fsa-trainer-skills",
                hint="pass --force to adopt and overwrite it, or --name/--dir to install elsewhere",
            )
    if existing is not None and existing.skill_name and existing.skill_name != name:
        raise UnmanagedDestinationError(
            f"{dest} holds the skill {existing.skill_name!r}, not {name!r}"
        )

    plan = planner.build_plan(dest, payload, existing, __version__)

    if existing is not None and existing.version == __version__ and not plan.changed:
        label = f"{skill.name}: {platform.label} ({scope})"
        print(f"{label}: already installed at {__version__} — {dest}")
        return

    label = f"{skill.name}: {platform.label} ({scope})"
    if args.dry_run:
        verb = "would install" if existing is None else "would update"
        print(f"{label}: {verb} {name} {__version__} -> {dest}")
        print_plan(plan, verbose=args.verbose)
        return

    apply_plan(dest, payload, plan, force=args.force)

    written = receipt_mod.Receipt(
        version=__version__,
        skill_name=name,
        platform=platform.key,
        scope=scope,
        dest=str(dest),
        installed_at=receipt_mod.utc_now(),
        installed_by=receipt_mod.installed_by(),
        cli=receipt_mod.cli_invocation(),
        dirs=plan.dirs,
        files=_file_records(dest, plan, force=args.force),
        venv=str(_venv_hint(skill)),
    )
    receipt_mod.write(dest, written)

    verb = "installed" if existing is None else f"updated {existing.version} ->"
    print(f"{label}: {verb} {__version__} at {dest}")
    print_plan(plan, verbose=args.verbose)
    _report_conflicts(plan, force=args.force)


def apply_plan(dest: Path, payload: Path, plan: Plan, *, force: bool) -> None:
    """Write the payload into `dest` via a staged swap."""
    preserved = planner.preserved_paths(dest, plan) if dest.exists() else []
    conflicts = {e.path for e in plan.conflicts}

    def build(staging: Path) -> None:
        for entry in plan.entries:
            if entry.action is Action.REMOVE:
                continue
            if not entry.payload_hash:
                continue
            src = payload / entry.path
            dst = staging / entry.path
            if entry.action is Action.CONFLICT and not force:
                # Keep the user's file; drop ours next to it for comparison.
                fsops.copy_file(dest / entry.path, dst)
                fsops.copy_file(src, staging / (entry.path + ".new"))
                continue
            if entry.action is Action.CONFLICT and force:
                fsops.copy_file(dest / entry.path, staging / (entry.path + ".bak"))
            fsops.copy_file(src, dst)

        for rel in preserved:
            if rel in conflicts:
                continue
            source = dest / rel
            if source.is_file():
                fsops.copy_file(source, staging / rel)

        for rel in plan.dirs:
            (staging / rel).mkdir(parents=True, exist_ok=True)

    fsops.staged_swap(dest, build)


def _file_records(dest: Path, plan: Plan, *, force: bool) -> list[receipt_mod.FileRecord]:
    """Record only the files we actually own.

    A conflict we chose not to overwrite is the user's file sitting at our path.
    Claiming it in the receipt would mean `uninstall` deletes their content, and
    the next `update` would stop noticing the conflict. So we leave it out: it
    stays theirs, and it keeps being reported as a conflict until they resolve
    it or pass --force.
    """
    records = []
    for entry in plan.entries:
        if not entry.payload_hash or entry.action is Action.REMOVE:
            continue
        if entry.action is Action.CONFLICT and not force:
            continue
        path = dest / entry.path
        if not path.is_file():
            continue
        stat = path.stat()
        records.append(
            receipt_mod.FileRecord(
                path=entry.path,
                sha256=fsops.sha256_file(path),
                bytes=stat.st_size,
                mode=oct(stat.st_mode & 0o777)[2:].rjust(4, "0"),
            )
        )
    return records


def _report_conflicts(plan: Plan, *, force: bool) -> None:
    conflicts = plan.conflicts
    if not conflicts:
        return
    if force:
        print(f"  {len(conflicts)} modified file(s) overwritten; previous bytes kept as *.bak")
        return
    print(f"  {len(conflicts)} file(s) you had modified were left as-is:")
    for entry in conflicts:
        print(f"    {entry.path}  (new version written to {entry.path}.new)")
    print("  re-run with --force to take the shipped version instead")


def _venv_hint(skill: Skill) -> Path:
    from ..envmgr import stamp

    return stamp.venv_path((skill.dep_group,))


def _prewarm(skills: list[Skill], args: argparse.Namespace) -> None:
    """Build each selected skill's venv now, so an offline machine stays
    self-sufficient later. Dependency groups are deduped across skills that
    share one, so two skills both needing "core" don't build it twice."""
    from ..envmgr import bootstrap

    for group in sorted({skill.dep_group for skill in skills}):
        try:
            bootstrap.ensure(group, offline=args.offline)
        except FsaTrainerSkillsError as exc:
            print(f"WARNING: could not pre-build the {group!r} environment: {exc.message}")


def uninstall_tree(dest: Path) -> None:  # pragma: no cover - used by tests/cleanup
    shutil.rmtree(dest, ignore_errors=True)


__all__ = ["add_parser", "apply_plan", "run"]
