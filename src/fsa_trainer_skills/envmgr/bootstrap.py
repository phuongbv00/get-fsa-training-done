"""Create and provision the managed venv.

Creation prefers `uv` when it is on PATH (an order of magnitude faster) and
falls back to `python -m venv`. When the requested groups need no third-party
packages we pass `--without-pip`, which skips `ensurepip` entirely: creation
becomes a fast, fully offline operation.

Installation always tries the vendored wheels first (`--no-index --find-links`).
It only reaches the network if a wheel is genuinely missing, and `--offline`
turns that into a hard error rather than a surprise download on an exam machine.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ..errors import EnvironmentError_
from . import stamp

LOCK_TIMEOUT_SECONDS = 300
LOCK_POLL_SECONDS = 0.2


def _uv() -> str | None:
    return shutil.which("uv")


def _run(cmd: list[str], *, what: str) -> None:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        raise EnvironmentError_(f"{what} failed to start: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise EnvironmentError_(
            f"{what} failed (exit {proc.returncode})",
            hint=detail.splitlines()[-1] if detail else None,
        )


class _DirLock:
    """Cheap cross-process lock so two concurrent runs don't build the same venv."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.acquired = False

    def __enter__(self) -> _DirLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self.acquired = True
                return self
            except FileExistsError:
                if self._stale():
                    self.path.unlink(missing_ok=True)
                    continue
                if time.monotonic() > deadline:
                    raise EnvironmentError_(
                        f"timed out waiting for the environment lock at {self.path}",
                        hint="delete that file if no other fsa-trainer-skills process is running",
                    ) from None
                time.sleep(LOCK_POLL_SECONDS)

    def _stale(self) -> bool:
        try:
            age = time.time() - self.path.stat().st_mtime
        except OSError:
            return False
        return age > LOCK_TIMEOUT_SECONDS

    def __exit__(self, *exc_info: object) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)


def _create(venv: Path, needs_pip: bool) -> str:
    venv.parent.mkdir(parents=True, exist_ok=True)
    if venv.exists():
        shutil.rmtree(venv, ignore_errors=True)

    uv = _uv()
    if uv:
        cmd = [uv, "venv", "--python", stamp.base_python(), str(venv)]
        if not needs_pip:
            # uv venvs have no pip by default, which is what we want here.
            pass
        _run(cmd, what="uv venv")
        version = subprocess.run([uv, "--version"], capture_output=True, text=True).stdout.strip()
        return version or "uv"

    cmd = [stamp.base_python(), "-m", "venv"]
    if not needs_pip:
        cmd.append("--without-pip")
    cmd.append(str(venv))
    _run(cmd, what="python -m venv")
    return f"python{sys.version_info[0]}.{sys.version_info[1]} -m venv"


def _install(venv: Path, group: str, *, offline: bool) -> None:
    requirements = stamp.requirement_lines(group)
    if not requirements:
        return

    wheels = stamp.WHEELS_DIR
    target_python = str(stamp.venv_python(venv))
    uv = _uv()

    if uv:
        base = [uv, "pip", "install", "--python", target_python]
    else:
        base = [target_python, "-m", "pip", "install", "--disable-pip-version-check", "--no-input"]

    offline_cmd = base + [
        "--no-index",
        "--find-links",
        str(wheels),
        "-r",
        str(stamp.requirements_file(group)),
    ]
    try:
        _run(offline_cmd, what=f"installing the '{group}' dependencies from vendored wheels")
        return
    except EnvironmentError_:
        if offline:
            raise EnvironmentError_(
                f"cannot provision the '{group}' dependencies offline",
                hint=(
                    f"vendored wheels in {wheels} do not satisfy "
                    f"{', '.join(requirements)}; rerun without --offline"
                ),
            ) from None

    _run(
        base + ["-r", str(stamp.requirements_file(group))],
        what=f"installing the '{group}' dependencies",
    )


def ensure(*groups: str, offline: bool = False) -> Path:
    """Return a venv that satisfies `groups`, building it if necessary."""
    requested = tuple(sorted(set(groups) or {"core"}))
    for group in requested:
        stamp.requirements_file(group)  # raises on an unknown group

    venv = stamp.venv_path(requested)
    if stamp.stamp_ok(venv, requested):
        return venv

    lock = venv.parent / f"{venv.name}.lock"
    with _DirLock(lock):
        if stamp.stamp_ok(venv, requested):
            return venv
        needs_pip = any(stamp.requirement_lines(group) for group in requested)
        creator = _create(venv, needs_pip)
        for group in requested:
            _install(venv, group, offline=offline)
        stamp.write_stamp(venv, requested, creator)
    return venv


def purge() -> list[Path]:
    """Delete every managed venv. Returns what was removed."""
    root = stamp.home() / "venvs"
    if not root.is_dir():
        return []
    removed = []
    for child in sorted(root.iterdir()):
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
            removed.append(child)
        elif child.suffix == ".lock":
            child.unlink(missing_ok=True)
    return removed


def info() -> dict:
    core = stamp.venv_path(("core",))
    return {
        "home": str(stamp.home()),
        "base_python": stamp.base_python(),
        "uv": _uv() or "",
        "in_venv": os.environ.get("FSA_TRAINER_SKILLS_IN_VENV") == "1",
        "groups": {
            "core": {
                "path": str(core),
                "ready": stamp.stamp_ok(core, ("core",)),
                "requirements": stamp.requirement_lines("core"),
            },
        },
    }
