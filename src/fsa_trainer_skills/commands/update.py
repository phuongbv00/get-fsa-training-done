"""`fsa-trainer-skills update` — version-aware upgrade of an installed skill."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..__about__ import __version__
from ..errors import FsaTrainerSkillsError, NotInstalledError
from ..install import migrations, planner
from ..install import receipt as receipt_mod
from ..platforms.base import Platform
from ..skillkit import Skill
from .common import (
    add_target_args,
    print_plan,
    resolve_skills,
    resolve_targets,
    validate_payload_or_die,
)
from .install import _file_records, _report_conflicts, _venv_hint, apply_plan


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "update",
        help="upgrade an installed skill to this package's version",
        description=(
            "Compare the installed files against the bundled payload and apply the "
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
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    skills = resolve_skills(args)
    exit_code = 0

    for skill in skills:
        payload = skill.payload_dir
        if not args.check:
            validate_payload_or_die(payload)

        for platform, scope, dest in resolve_targets(args, skill):
            try:
                outdated = _update_one(skill, platform, scope, dest, args, payload)
                if args.check and outdated:
                    exit_code = 1
            except FsaTrainerSkillsError as exc:
                exit_code = max(exit_code, exc.exit_code)
                print(f"ERROR: {skill.name}: {platform.label} ({scope}): {exc.message}")
                if exc.hint:
                    print(f"       {exc.hint}")
    return exit_code


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
            f"{dest} is not managed by fsa-trainer-skills",
            hint="run `fsa-trainer-skills install` (add --force to adopt an existing directory)",
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
