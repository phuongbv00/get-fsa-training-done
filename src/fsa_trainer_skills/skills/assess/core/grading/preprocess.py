"""Extract and normalise submissions into one canonical folder per trainee.

Layout produced:

    <out>/<SUBJECT>_<TYPE>_<STDID>/

A trainee who submitted several archives gets one subfolder per archive; a lone
archive is flattened straight into their folder. Nothing under `--src` is
touched — the raw uploads stay exactly as they arrived.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from fsa_trainer_skills.errors import MissingToolError

from . import roster as roster_mod
from .roster import Roster

JUNK = {"__MACOSX", ".DS_Store", "Thumbs.db", ".git"}
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z"}

#: Extractors by archive type, tried in order. `ditto` is macOS-only and
#: handles resource forks best; the rest cover Linux.
ZIP_EXTRACTORS = (
    ["ditto", "-x", "-k", "{archive}", "{dest}"],
    ["unzip", "-o", "-qq", "{archive}", "-d", "{dest}"],
    ["bsdtar", "-xf", "{archive}", "-C", "{dest}"],
)
OTHER_EXTRACTORS = (
    ["bsdtar", "-xf", "{archive}", "-C", "{dest}"],
    ["7z", "x", "-y", "-o{dest}", "{archive}"],
    ["unar", "-q", "-o", "{dest}", "{archive}"],
)


@dataclass
class Outcome:
    created: list[tuple[str, bool, bool]] = field(default_factory=list)
    skipped_dropped: list[tuple[str, str]] = field(default_factory=list)
    failures: list[tuple[str, str]] = field(default_factory=list)
    missing: list[tuple[str, str]] = field(default_factory=list)


def meaningful(directory: Path) -> list[Path]:
    return [
        path
        for path in sorted(directory.iterdir())
        if path.name not in JUNK and not path.name.startswith("._")
    ]


def content_root(directory: Path) -> Path:
    """Descend through redundant single-folder nesting."""
    current = directory
    while True:
        children = meaningful(current)
        if len(children) == 1 and children[0].is_dir():
            current = children[0]
        else:
            return current


def extract(archive: Path, dest: Path) -> tuple[bool, str]:
    templates = ZIP_EXTRACTORS if archive.suffix.lower() == ".zip" else OTHER_EXTRACTORS
    last_error = ""
    tried_any = False
    for template in templates:
        if shutil.which(template[0]) is None:
            continue
        tried_any = True
        command = [part.format(archive=str(archive), dest=str(dest)) for part in template]
        completed = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        if completed.returncode == 0 and any(dest.iterdir()):
            return True, template[0]
        last_error = f"{template[0]}: {completed.stdout.strip()[:200]}"

    if not tried_any:
        names = ", ".join(sorted({t[0] for t in ZIP_EXTRACTORS + OTHER_EXTRACTORS}))
        raise MissingToolError(
            f"no archive extractor found for {archive.name}",
            hint=f"install one of: {names}",
        )
    return False, last_error or "no extractor succeeded"


def copy_into(root: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for path in meaningful(root):
        destination = target / path.name
        if path.is_dir():
            shutil.copytree(
                path,
                destination,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(*JUNK, "._*"),
            )
        else:
            shutil.copy2(path, destination)


def gather_sources(src: Path, out: Path) -> list[Path]:
    sources = []
    for path in sorted(src.iterdir()):
        if path.name in JUNK or path.name.startswith((".", "_")) or path == out:
            continue
        if path.is_file() and path.suffix.lower() in ARCHIVE_EXTENSIONS:
            sources.append(path)
        elif path.is_dir() and path.name != out.name:
            sources.append(path)
    return sources


def run(
    *,
    roster: Roster,
    src: Path,
    out: Path,
    subject: str,
    submission_type: str,
) -> Outcome:
    subject = subject.upper()
    submission_type = submission_type.upper()
    out.mkdir(parents=True, exist_ok=True)
    outcome = Outcome()

    # Clear folders for trainees who dropped after an earlier run, so the batch
    # planner cannot pick them up again.
    for lowered in roster.dropped_ids:
        trainee = roster.get(lowered)
        canonical = trainee.std_id if trainee else lowered
        stale = out / roster_mod.folder_name(subject, submission_type, canonical)
        if stale.exists():
            shutil.rmtree(stale)

    by_student: dict[str, list[tuple[Path, bool]]] = {}
    for source in gather_sources(src, out):
        stem = source.stem if source.is_file() else source.name
        std_id, known = roster_mod.match_std_id(stem, roster)
        if known and roster.is_dropped(std_id):
            outcome.skipped_dropped.append((std_id, source.name))
            continue
        by_student.setdefault(std_id, []).append((source, known))

    for std_id, items in sorted(by_student.items()):
        known = items[0][1]
        folder = out / roster_mod.folder_name(subject, submission_type, std_id)
        if folder.exists():
            shutil.rmtree(folder)
        multiple = len(items) > 1

        for source, _ in items:
            staging = Path(tempfile.mkdtemp(prefix="fsa-trainer-skills-extract-"))
            try:
                if source.is_file():
                    extracted, info = extract(source, staging)
                    if not extracted:
                        outcome.failures.append((source.name, info))
                        continue
                    root = content_root(staging)
                else:
                    root = content_root(source)
                copy_into(root, folder / source.stem if multiple else folder)
            finally:
                shutil.rmtree(staging, ignore_errors=True)

        if folder.exists():
            outcome.created.append((std_id, known, multiple))

    submitted = {std_id for std_id, known, _ in outcome.created if known}
    outcome.missing = [
        (trainee.std_id, trainee.name)
        for trainee in roster.active
        if trainee.std_id not in submitted
    ]
    return outcome
