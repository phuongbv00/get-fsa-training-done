"""Upgrade the CLI itself from PyPI before `gftd update` touches a skill.

The skill's files ship inside the package, so `gftd update` alone can only
reinstall the payload it already carries. This module asks PyPI for the latest
release, upgrades the package the way it was installed (pip, pipx or
`uv tool`), and hands the rest of `update` to the new version in a fresh
interpreter. An editable checkout, or a run straight from source, is left
alone: upgrading it is `git pull`, not pip's job.

Stdlib only — `update` must run on a bare interpreter.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from importlib import metadata
from pathlib import Path

from ..__about__ import PACKAGE_NAME, __version__
from ..errors import EnvironmentError_

PYPI_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
TIMEOUT_SECONDS = 10
#: Set to 1 to skip the PyPI check everywhere (CI, air-gapped machines, tests).
DISABLE_ENV = "GET_FSA_TRAINING_DONE_NO_SELF_UPDATE"


def disabled() -> bool:
    return os.environ.get(DISABLE_ENV, "") not in ("", "0")


def latest_version() -> str | None:
    """The newest release on PyPI, or None when PyPI cannot be reached."""
    try:
        with urllib.request.urlopen(PYPI_URL, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)["info"]["version"]
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def _key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version.split("+")[0])[:3])


def is_newer(candidate: str, current: str = __version__) -> bool:
    return _key(candidate) > _key(current)


def install_kind() -> str:
    """How this package was installed: pipx, uv-tool, pip, editable or source."""
    try:
        dist = metadata.distribution(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return "source"
    direct_url = dist.read_text("direct_url.json")
    if direct_url:
        try:
            if json.loads(direct_url).get("dir_info", {}).get("editable"):
                return "editable"
        except ValueError:
            pass
    # A checkout on PYTHONPATH can shadow an unrelated installed copy.
    installed = Path(str(dist.locate_file("get_fsa_training_done"))).resolve()
    if installed != Path(__file__).resolve().parents[1]:
        return "source"
    prefix = sys.prefix.replace("\\", "/")
    if "/pipx/venvs/" in prefix:
        return "pipx"
    if "/uv/tools/" in prefix:
        return "uv-tool"
    return "pip"


def upgrade_command(kind: str, version: str) -> list[str]:
    if kind == "pipx" and (pipx := shutil.which("pipx")):
        return [pipx, "upgrade", PACKAGE_NAME]
    if kind == "uv-tool" and (uv := shutil.which("uv")):
        return [uv, "tool", "upgrade", PACKAGE_NAME]
    pinned = f"{PACKAGE_NAME}=={version}"
    has_pip = (
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True).returncode
        == 0
    )
    if not has_pip and (uv := shutil.which("uv")):
        return [uv, "pip", "install", "--python", sys.executable, "--upgrade", pinned]
    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--disable-pip-version-check",
        "--no-input",
        pinned,
    ]


def upgrade(kind: str, version: str) -> None:
    cmd = upgrade_command(kind, version)
    print(f"{PACKAGE_NAME}: upgrading {__version__} -> {version} ({' '.join(cmd)})")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        raise EnvironmentError_(f"upgrading {PACKAGE_NAME} failed to start: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise EnvironmentError_(
            f"upgrading {PACKAGE_NAME} from PyPI failed (exit {proc.returncode})",
            hint=(detail.splitlines()[-1] if detail else None)
            or "upgrade it by hand, then rerun with --no-self-update",
        )


def rerun(argv: list[str]) -> int:
    """Run `update` again under the freshly installed package."""
    cmd = [sys.executable, "-m", "get_fsa_training_done", *argv, "--no-self-update"]
    return subprocess.run(cmd).returncode
