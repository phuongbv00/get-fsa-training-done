"""Venv identity and the stamp file that makes re-runs nearly free.

The venv path is keyed on the base interpreter's *realpath*, the package
version, and a hash of the requirement files. A pyenv shim flip, a Homebrew
Python upgrade, or a package upgrade therefore lands on a fresh venv instead of
silently reusing a broken one.

Checking whether a venv is usable is two `stat`s and one small JSON read — no
subprocess, no import of the dependency, no network. That matters because the
check runs on every single worker invocation.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from ...__about__ import PACKAGE_NAME, __version__

STAMP_NAME = ".get-fsa-training-done-stamp.json"
SCHEMA = 1

REQUIREMENTS_DIR = Path(__file__).resolve().parent / "requirements"
WHEELS_DIR = Path(__file__).resolve().parent / "wheels"

GROUPS = ("core",)


def requirements_file(group: str) -> Path:
    path = REQUIREMENTS_DIR / f"{group}.txt"
    if not path.is_file():
        raise ValueError(f"unknown dependency group: {group!r}")
    return path


def requirement_lines(group: str) -> list[str]:
    """Non-comment, non-blank lines — the actual pins."""
    text = requirements_file(group).read_text(encoding="utf-8")
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def requirements_hash(group: str) -> str:
    payload = "\n".join(requirement_lines(group)).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def base_python() -> str:
    """The interpreter we would build a venv from.

    When we are already inside a managed venv (a re-exec), resolve back to the
    interpreter that created it so the key stays stable across re-execs.
    """
    base = getattr(sys, "_base_executable", None) or sys.executable
    return os.path.realpath(base)


def home() -> Path:
    override = os.environ.get("GET_FSA_TRAINING_DONE_HOME")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local) / PACKAGE_NAME
    cache = os.environ.get("XDG_CACHE_HOME")
    root = Path(cache).expanduser() if cache else Path.home() / ".cache"
    return root / PACKAGE_NAME


def venv_key(groups: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    digest.update(base_python().encode("utf-8"))
    digest.update(b"|")
    digest.update(__version__.encode("utf-8"))
    for group in sorted(groups):
        digest.update(b"|")
        digest.update(group.encode("utf-8"))
        digest.update(requirements_hash(group).encode("utf-8"))
    return f"py{sys.version_info[0]}.{sys.version_info[1]}-{digest.hexdigest()[:12]}"


def venv_path(groups: tuple[str, ...]) -> Path:
    return home() / "venvs" / venv_key(groups)


def venv_python(venv: Path) -> Path:
    if sys.platform == "win32":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def stamp_path(venv: Path) -> Path:
    return venv / STAMP_NAME


def read_stamp(venv: Path) -> dict | None:
    path = stamp_path(venv)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def stamp_ok(venv: Path, groups: tuple[str, ...]) -> bool:
    if not venv_python(venv).exists():
        return False
    data = read_stamp(venv)
    if not data or data.get("package_version") != __version__:
        return False
    recorded = data.get("groups", {})
    return all(recorded.get(group) == requirements_hash(group) for group in groups)


def write_stamp(venv: Path, groups: tuple[str, ...], creator: str) -> None:
    existing = read_stamp(venv) or {}
    recorded = dict(existing.get("groups", {}))
    recorded.update({group: requirements_hash(group) for group in groups})
    stamp_path(venv).write_text(
        json.dumps(
            {
                "schema": SCHEMA,
                "package_version": __version__,
                "base_python": base_python(),
                "python_version": ".".join(str(p) for p in sys.version_info[:3]),
                "groups": recorded,
                "creator": creator,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
