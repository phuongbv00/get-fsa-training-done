"""Version-to-version fixups that a file diff cannot express.

A migration runs after the payload has been written, when upgrading *from* a
version matching its `applies_from`. Renames are the usual case: the old file is
gone from the payload so the planner marks it REMOVE, but if the user edited it
the planner marks it CONFLICT and leaves it — a migration can say "that is a
rename, not a conflict" and clean up.

Empty while no shipped version has renamed or moved a payload file in a way
the planner cannot reconcile.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Migration:
    #: Applies when the previously installed version is < `applies_before`.
    applies_before: str
    description: str
    run: Callable[[Path], list[str]]


MIGRATIONS: list[Migration] = []


def _version_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in version.split(".")[:3]:
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def pending(old_version: str | None) -> list[Migration]:
    if not old_version:
        return []
    old = _version_tuple(old_version)
    return [m for m in MIGRATIONS if old < _version_tuple(m.applies_before)]


def run_all(dest: Path, old_version: str | None) -> list[str]:
    notes: list[str] = []
    for migration in pending(old_version):
        notes.extend(migration.run(dest))
    return notes
