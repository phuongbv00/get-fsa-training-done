"""Finding and clearing installs left behind when a skill was renamed.

A skill's installed directory is named after `Skill.name`, so renaming one
orphans the old directory. That is worse than untidy: Claude Code and Codex load
every directory under `skills/`, so the stale copy keeps advertising the same
triggers as the new one and the agent sees two skills competing for the same
request. Nothing at runtime reports this — both simply exist.

So `install` and `update` look for the old names and clear them, using the same
receipt-scoped removal `uninstall` uses: a file the user edited is kept and
reported, never deleted on their behalf. A directory is only ever touched when
its own receipt says it holds a name this skill used to have, which is what
stops an unrelated folder that happens to share a name from being removed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..platforms.base import Platform
from ..skillkit import Skill
from . import receipt as receipt_mod
from . import removal


@dataclass(frozen=True)
class LegacyInstall:
    name: str
    dest: Path
    receipt: receipt_mod.Receipt


def find(
    skill: Skill,
    platform: Platform,
    scope: str,
    project_root: Path | None,
    *,
    current_dest: Path,
) -> list[LegacyInstall]:
    """Installs under this skill's previous names, in the same root."""
    found: list[LegacyInstall] = []
    for previous in skill.previous_names:
        dest = platform.dest(scope, previous, project_root)
        if dest == current_dest or not dest.is_dir():
            continue
        receipt = receipt_mod.read(dest)
        # No receipt means we did not install it; a receipt naming something
        # else means it belongs to another skill. Neither is ours to remove.
        if receipt is None or receipt.skill_name != previous:
            continue
        found.append(LegacyInstall(name=previous, dest=dest, receipt=receipt))
    return found


def clean(legacy: LegacyInstall, *, dry_run: bool) -> list[str]:
    """Remove a legacy install, returning lines describing what happened."""
    if dry_run:
        to_delete, kept = removal.classify_recorded(legacy.dest, legacy.receipt)
        lines = [f"would remove the superseded {legacy.name} install at {legacy.dest}"]
        lines.append(f"  {len(to_delete)} file(s) would be removed")
        if kept:
            lines.append(f"  {len(kept)} modified file(s) would be kept")
        return lines

    removed, leftovers = removal.remove_recorded(legacy.dest, legacy.receipt)
    lines = [f"removed the superseded {legacy.name} install at {legacy.dest}"]
    if leftovers:
        lines.append(f"  kept {len(leftovers)} file(s) you had modified in {legacy.dest}")
        for rel in leftovers[:10]:
            lines.append(f"    kept {rel.as_posix()}")
        if len(leftovers) > 10:
            lines.append(f"    ... and {len(leftovers) - 10} more")
    else:
        lines[0] = f"removed the superseded {legacy.name} install ({len(removed)} files)"
    return lines


__all__ = ["LegacyInstall", "clean", "find"]
