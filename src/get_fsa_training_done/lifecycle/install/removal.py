"""Removing exactly what a receipt vouches for, and nothing else.

A file the user edited is theirs: its hash no longer matches the receipt, so it
is kept and reported rather than deleted. Anything that removes an install goes
through here, so no path can be the careless one.
"""

from __future__ import annotations

from pathlib import Path

from . import fsops
from . import receipt as receipt_mod


def classify_recorded(dest: Path, receipt: receipt_mod.Receipt) -> tuple[list[str], list[str]]:
    """Split the receipt's files into ours to delete, and edited ones to keep."""
    to_delete: list[str] = []
    kept: list[str] = []
    for record in receipt.files:
        path = dest / record.path
        if not path.is_file():
            continue
        if fsops.sha256_file(path) == record.sha256:
            to_delete.append(record.path)
        else:
            kept.append(record.path)
    return to_delete, kept


def remove_recorded(dest: Path, receipt: receipt_mod.Receipt) -> tuple[list[str], list[Path]]:
    """Delete the unmodified files, drop the receipt, and tidy empty directories.

    Returns what was deleted and what is still there afterwards.
    """
    to_delete, _ = classify_recorded(dest, receipt)
    for rel in to_delete:
        (dest / rel).unlink(missing_ok=True)
    receipt_mod.receipt_path(dest).unlink(missing_ok=True)
    fsops.prune_empty_dirs(dest, [Path(d) for d in receipt.dirs])

    leftovers = fsops.walk_files(dest)
    if not leftovers and dest.is_dir():
        try:
            rmdir_tree(dest)
        except OSError:
            pass
    return to_delete, leftovers


def rmdir_tree(root: Path) -> None:
    """Remove `root` and any empty directories under it, bottom-up."""
    for path in sorted(
        (p for p in root.rglob("*") if p.is_dir()),
        key=lambda p: len(p.parts),
        reverse=True,
    ):
        if not any(path.iterdir()):
            path.rmdir()
    if not any(root.iterdir()):
        root.rmdir()


__all__ = ["classify_recorded", "remove_recorded", "rmdir_tree"]
