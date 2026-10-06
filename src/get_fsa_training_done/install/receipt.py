"""The install receipt: `<dest>/.get-fsa-training-done-install.json`.

It lives *inside* the installed skill directory rather than in a central state
file so that `update` and `uninstall` keep working when the folder was copied by
hand, synced to another machine, or when the user's cache was wiped. It is a
dotfile at the payload root, which neither Claude Code nor Codex reads and which
Codex's validator ignores.

`cli.invocation` is the field that earns its keep: `npx get-fsa-training-done install`
leaves nothing on `PATH`, so the skill would have no way to call back into the
CLI afterwards. Recording an absolute, replayable invocation at install time
means the skill never has to guess.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import platform as _platform
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..__about__ import CLI_NAME, PACKAGE_NAME, __version__

RECEIPT_NAME = ".get-fsa-training-done-install.json"
SCHEMA = 1


@dataclass
class FileRecord:
    path: str
    sha256: str
    bytes: int
    mode: str

    @classmethod
    def from_dict(cls, data: dict) -> FileRecord:
        return cls(
            path=data["path"],
            sha256=data["sha256"],
            bytes=int(data.get("bytes", 0)),
            mode=data.get("mode", "0644"),
        )


@dataclass
class Receipt:
    version: str
    skill_name: str
    platform: str
    scope: str
    dest: str
    installed_at: str
    cli: dict = field(default_factory=dict)
    dirs: list[str] = field(default_factory=list)
    files: list[FileRecord] = field(default_factory=list)
    venv: str = ""
    schema: int = SCHEMA
    package: str = PACKAGE_NAME
    installed_by: str = ""

    def to_json(self) -> str:
        data = asdict(self)
        ordered = {
            "schema": data["schema"],
            "package": data["package"],
            "version": data["version"],
            "skill_name": data["skill_name"],
            "platform": data["platform"],
            "scope": data["scope"],
            "dest": data["dest"],
            "installed_at": data["installed_at"],
            "installed_by": data["installed_by"],
            "cli": data["cli"],
            "dirs": data["dirs"],
            "files": data["files"],
            "venv": data["venv"],
        }
        return json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"

    @classmethod
    def from_dict(cls, data: dict) -> Receipt:
        return cls(
            schema=int(data.get("schema", SCHEMA)),
            package=data.get("package", PACKAGE_NAME),
            version=data.get("version", "0.0.0"),
            skill_name=data.get("skill_name", ""),
            platform=data.get("platform", ""),
            scope=data.get("scope", ""),
            dest=data.get("dest", ""),
            installed_at=data.get("installed_at", ""),
            installed_by=data.get("installed_by", ""),
            cli=data.get("cli", {}),
            dirs=list(data.get("dirs", [])),
            files=[FileRecord.from_dict(f) for f in data.get("files", [])],
            venv=data.get("venv", ""),
        )

    def file_hashes(self) -> dict[str, str]:
        return {f.path: f.sha256 for f in self.files}


def receipt_path(dest: Path) -> Path:
    return dest / RECEIPT_NAME


def read(dest: Path) -> Receipt | None:
    path = receipt_path(dest)
    if not path.is_file():
        return None
    try:
        return Receipt.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def write(dest: Path, receipt: Receipt) -> None:
    receipt_path(dest).write_text(receipt.to_json(), encoding="utf-8")


def utc_now() -> str:
    return (
        _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )


def installed_by() -> str:
    impl = _platform.python_implementation()
    pyver = _platform.python_version()
    return f"{PACKAGE_NAME} {__version__} ({impl} {pyver}, {sys.platform})"


def cli_invocation() -> dict:
    """How to re-invoke this CLI later, from inside the installed skill.

    The interpreter path is absolute and `PYTHONPATH` names the directory the
    package was imported from, so this works for pip, pipx, an editable
    checkout, and the npm shim alike.
    """
    from shutil import which

    package_parent = str(Path(__file__).resolve().parents[2])
    return {
        "invocation": [os.path.realpath(sys.executable), "-m", "get_fsa_training_done"],
        "pythonpath": package_parent,
        "on_path": CLI_NAME if which(CLI_NAME) else "",
    }
