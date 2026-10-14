"""Symlinks from an agent's skills folder into the shared `.agents/skills` copy.

A link is only ever created, replaced or removed when it is a symlink: nothing
here deletes a real directory. A relative target keeps a project's links valid
when the repository is moved or cloned.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def points_to(link: Path, target: Path) -> bool:
    """`link` is a symlink that resolves to `target`."""
    if not link.is_symlink():
        return False
    try:
        return link.resolve() == target.resolve()
    except OSError:
        return False


def make(link: Path, target: Path) -> None:
    """Point `link` at `target`, replacing a symlink already at `link`.

    Raises OSError when the filesystem or the OS refuses symlinks (Windows
    without Developer Mode, some network shares); the caller copies instead.
    """
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        link.unlink()
    elif link.is_dir() and not any(link.iterdir()):
        link.rmdir()
    relative = os.path.relpath(target, link.parent)
    os.symlink(relative, link, target_is_directory=True)


def remove(link: Path) -> bool:
    """Remove `link` if it is a symlink; never touches a real directory."""
    if link.is_symlink():
        link.unlink()
        return True
    return False


_SUPPORTED: bool | None = None


def supported() -> bool:
    """Whether this machine lets an unprivileged process create directory symlinks."""
    global _SUPPORTED
    if _SUPPORTED is None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            try:
                os.symlink(target, Path(tmp) / "link", target_is_directory=True)
                _SUPPORTED = True
            except (OSError, NotImplementedError):
                _SUPPORTED = False
    return _SUPPORTED


__all__ = ["make", "points_to", "remove", "supported"]
