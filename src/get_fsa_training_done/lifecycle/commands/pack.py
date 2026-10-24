"""`gftd pack` — the skill as a zip to upload to a hosted agent.

A hosted agent — Claude Managed Agents, the Claude API's code execution, a
claude.ai workspace — never reads a folder on your machine: it takes a skill as
an upload, a directory holding `SKILL.md` at its root, sent as a zip. The zip
holds one folder, named after the skill, with the payload exactly as `install`
writes it and no receipt: the receipt names an interpreter on this machine,
and the sandbox gets its CLI from `scripts/setup.sh` instead.

The archive is reproducible — entries sorted, timestamps fixed — so the same
version always packs to the same bytes.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from ...__about__ import __version__
from ...errors import GftdError
from ...skill import SKILL
from ..install import fsops, receipt
from .common import validate_payload_or_die

#: The Skills API refuses an upload this large or larger, uncompressed.
MAX_BYTES = 30 * 1024 * 1024
#: Words the Skills API refuses in a skill's name.
RESERVED_WORDS = ("anthropic", "claude")
#: 1980-01-01, the earliest time a zip entry can carry.
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "pack",
        help="write the skill as a zip to upload to a hosted agent (Claude Managed Agents)",
        description=(
            "Write the skill as a zip holding one folder with SKILL.md at its root, "
            "the shape the Skills API and the Claude Console take as an upload."
        ),
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help=f"the zip to write (default: ./{SKILL.name}-{__version__}.zip)",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    output = Path(args.output or f"{SKILL.name}-{__version__}.zip").expanduser()
    if output.suffix.lower() != ".zip":
        raise GftdError(f"{output} is not a .zip", hint="name the archive to write, ending in .zip")
    files, size = pack(output)
    print(
        f"{SKILL.name} {__version__}: packed {files} files ({_kib(size)} uncompressed) -> {output}"
    )
    return 0


def pack(output: Path) -> tuple[int, int]:
    """Write the zip; return how many files it holds and their size, uncompressed."""
    payload = SKILL.payload_dir
    validate_payload_or_die(payload)
    _check_name(SKILL.name)

    paths = [
        rel
        for rel in sorted(fsops.walk_files(payload), key=lambda p: p.as_posix())
        if rel.name != receipt.RECEIPT_NAME
    ]
    size = sum((payload / rel).stat().st_size for rel in paths)
    if size >= MAX_BYTES:
        raise GftdError(
            f"the skill is {_kib(size)} uncompressed; the Skills API takes under {_kib(MAX_BYTES)}"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel in paths:
            source = payload / rel
            info = zipfile.ZipInfo(f"{SKILL.name}/{rel.as_posix()}", date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if source.suffix == ".sh" else 0o644
            info.external_attr = (0o100000 | mode) << 16
            archive.writestr(info, source.read_bytes())
    return len(paths), size


def _check_name(name: str) -> None:
    for word in RESERVED_WORDS:
        if word in name:
            raise GftdError(f"the Skills API refuses a skill name containing {word!r}: {name}")


def _kib(size: int) -> str:
    return f"{size / 1024:.0f} KiB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} MiB"


__all__ = ["MAX_BYTES", "add_parser", "pack", "run"]
