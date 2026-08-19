"""Filesystem primitives shared by install/update/uninstall.

Two invariants everything else depends on:

* Bytes are copied verbatim — no line-ending translation. The Blooket CSV is
  CRLF; a helpful normalisation here would silently corrupt it, and the
  receipt hashes would stop matching what is on disk.
* Replacing a skill directory is a staged swap, so a crash mid-write leaves
  either the old tree or the new one, never a half-written mixture.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

CHUNK = 1 << 20


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def walk_files(root: Path) -> list[Path]:
    """Every file under `root`, as POSIX-relative paths, sorted."""
    if not root.is_dir():
        return []
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        base = Path(dirpath)
        for name in sorted(filenames):
            if name.endswith((".pyc", ".pyo")) or name == ".DS_Store":
                continue
            out.append((base / name).relative_to(root))
    return sorted(out, key=lambda p: p.as_posix())


def walk_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in dirnames:
            out.append((Path(dirpath) / name).relative_to(root))
    return sorted(out, key=lambda p: p.as_posix())


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    shutil.copymode(src, dst)


def staged_swap(dest: Path, build) -> None:
    """Replace `dest` with a freshly built tree, atomically enough to be safe.

    `build(staging_dir)` populates a sibling temp directory. We then rename the
    old tree aside, move the new one into place, and only after that succeeds
    delete the old. Any failure before the second rename rolls back.
    """
    parent = dest.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = parent / f".{dest.name}.fsa-trainer-skills.tmp"
    backup = parent / f".{dest.name}.fsa-trainer-skills.bak"

    for stale in (staging, backup):
        if stale.exists():
            shutil.rmtree(stale, ignore_errors=True)

    staging.mkdir(parents=True)
    try:
        build(staging)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    had_previous = dest.exists()
    if had_previous:
        os.rename(dest, backup)
    try:
        os.rename(staging, dest)
    except BaseException:
        if had_previous and not dest.exists():
            os.rename(backup, dest)
        shutil.rmtree(staging, ignore_errors=True)
        raise
    shutil.rmtree(backup, ignore_errors=True)


def prune_empty_dirs(root: Path, relatives: list[Path]) -> None:
    """Remove the listed directories, deepest first, while they are empty."""
    for rel in sorted(relatives, key=lambda p: len(p.parts), reverse=True):
        target = root / rel
        if target.is_dir() and not any(target.iterdir()):
            target.rmdir()
