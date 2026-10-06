"""`get-fsa-training-done uninstall` — remove exactly what was written, and nothing else."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ...errors import GftdError, UnmanagedDestinationError
from ...skill import SKILL, Skill
from ..install import receipt as receipt_mod
from ..install import removal
from ..platforms.base import Platform
from .common import add_target_args, resolve_targets


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "uninstall",
        help="remove an installed skill",
        description=(
            "Delete the files this tool installed. Files you added or edited are "
            "left in place unless --force is given."
        ),
    )
    add_target_args(parser)
    parser.add_argument(
        "--force",
        action="store_true",
        help="remove the whole directory, including files get-fsa-training-done did not write",
    )
    parser.add_argument(
        "--purge-venv",
        action="store_true",
        help="also delete the managed virtualenvs",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    skill = SKILL
    failures = 0
    removed_any = False

    for platform, scope, dest in resolve_targets(args, skill):
        try:
            if _uninstall_one(skill, platform, scope, dest, args):
                removed_any = True
        except GftdError as exc:
            failures += 1
            print(f"ERROR: {skill.name}: {platform.label} ({scope}): {exc.message}")
            if exc.hint:
                print(f"       {exc.hint}")

    if args.purge_venv and removed_any and not args.dry_run:
        from ..envmgr import bootstrap

        for path in bootstrap.purge():
            print(f"removed environment {path}")

    return 1 if failures else 0


def _uninstall_one(
    skill: Skill, platform: Platform, scope: str, dest: Path, args: argparse.Namespace
) -> bool:
    label = f"{skill.name}: {platform.label} ({scope})"
    if not dest.exists():
        print(f"{label}: nothing installed at {dest}")
        return False

    receipt = receipt_mod.read(dest)
    if receipt is None:
        if not (args.force and args.dir):
            raise UnmanagedDestinationError(
                f"{dest} has no get-fsa-training-done receipt",
                hint="if you are certain, re-run with both --dir and --force",
            )
        if args.dry_run:
            print(f"{label}: would remove the whole directory {dest} (unmanaged, forced)")
            return True
        shutil.rmtree(dest, ignore_errors=True)
        print(f"{label}: removed {dest} (unmanaged, forced)")
        return True

    if args.force:
        if args.dry_run:
            print(f"{label}: would remove the whole directory {dest}")
            return True
        shutil.rmtree(dest, ignore_errors=True)
        print(f"{label}: removed {dest}")
        return True

    to_delete, kept = removal.classify_recorded(dest, receipt)

    if args.dry_run:
        print(f"{label}: would remove {len(to_delete)} file(s) from {dest}")
        if kept:
            print(f"  {len(kept)} modified file(s) would be kept")
        return True

    to_delete, leftovers = removal.remove_recorded(dest, receipt)
    if not leftovers:
        print(f"{label}: removed {dest}")
    else:
        print(f"{label}: removed {len(to_delete)} file(s); kept {len(leftovers)} in {dest}")
        for rel in leftovers[:10]:
            print(f"    kept {rel.as_posix()}")
        if len(leftovers) > 10:
            print(f"    ... and {len(leftovers) - 10} more")
    return True
