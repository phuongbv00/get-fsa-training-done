"""Extract and normalise submissions into one canonical folder per trainee.

Layout produced:

    <out>/<SUBJECT>_<TYPE>_<STDID>/

A trainee who submitted several uploads gets one subfolder per upload; a lone
upload is flattened straight into their folder. An upload is an archive, a
folder, or a loose file such as a PDF or a single source file — a document
exam is submitted that way and must not vanish as "did not submit". Nothing
under `--src` is touched — the raw uploads stay exactly as they arrived.
"""

from __future__ import annotations

import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from get_fsa_training_done.errors import MissingToolError

from . import roster as roster_mod
from .roster import Roster

#: `.git` is deliberately not junk: for a Git-workflow assessment the history is
#: the evidence — branches, commits, a conflict committed with its markers — and
#: the working tree alone can say the opposite of what was committed. The cheat
#: checks skip `.git` themselves.
JUNK = {"__MACOSX", ".DS_Store", "Thumbs.db"}
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz"}

#: `.rar` is the one format with no pure-Python reader — it is proprietary and
#: `rarfile` only wraps an external binary anyway. Everything else is handled
#: in-process, so a grading machine needs nothing installed. These are tried in
#: order and only for `.rar`; `doctor` reports them as optional.
RAR_EXTRACTORS = (
    ["unar", "-q", "-o", "{dest}", "{archive}"],
    ["7z", "x", "-y", "-o{dest}", "{archive}"],
    ["bsdtar", "-xf", "{archive}", "-C", "{dest}"],
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


def _is_within(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _safe_members(names: list[str], dest: Path) -> list[str]:
    """Drop entries that would escape `dest`.

    The shell extractors refused traversal themselves; `zipfile.extractall` and
    `tarfile.extractall` historically did not, and these archives are untrusted
    — they are whatever a trainee uploaded. An entry that would land outside the
    trainee's folder is skipped rather than failing the whole submission, since
    the rest of the upload is still gradeable.
    """
    return [name for name in names if _is_within(dest, dest / name)]


def extract(archive: Path, dest: Path) -> tuple[bool, str]:
    """Unpack `archive` into `dest`. Returns (succeeded, what did it / why not)."""
    suffix = archive.suffix.lower()
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(dest, members=_safe_members(bundle.namelist(), dest))
            return True, "zipfile"

        if tarfile.is_tarfile(archive):
            with tarfile.open(archive) as bundle:
                safe = [m for m in bundle.getmembers() if _is_within(dest, dest / m.name)]
                # `filter="data"` also drops absolute paths, links pointing out
                # of the tree, and device nodes. It is the default from 3.14 and
                # absent before 3.11.4, so ask for it only when it exists.
                extra = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
                bundle.extractall(dest, members=safe, **extra)
            return True, "tarfile"

        if suffix == ".7z":
            try:
                import py7zr
            except ImportError as exc:  # pragma: no cover - the venv guarantees it
                raise MissingToolError(
                    "the .7z reader is not available in this environment",
                    hint="run `get-fsa-training-done install` to build the managed environment",
                ) from exc
            with py7zr.SevenZipFile(archive) as bundle:
                bundle.extract(path=dest, targets=_safe_members(bundle.getnames(), dest))
            return True, "py7zr"

        if suffix == ".rar":
            return _extract_rar(archive, dest)
    except MissingToolError:
        raise
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}".strip()[:200]

    return False, f"unrecognised archive format: {archive.name}"


def _extract_rar(archive: Path, dest: Path) -> tuple[bool, str]:
    last_error = ""
    for template in RAR_EXTRACTORS:
        if shutil.which(template[0]) is None:
            continue
        command = [part.format(archive=str(archive), dest=str(dest)) for part in template]
        completed = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        if completed.returncode == 0 and any(dest.iterdir()):
            return True, template[0]
        last_error = f"{template[0]}: {completed.stdout.strip()[:200]}"

    if not last_error:
        names = ", ".join(t[0] for t in RAR_EXTRACTORS)
        return False, (f".rar needs one of {names} on PATH — ask the trainee to resubmit as .zip")
    return False, last_error


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


def is_archive(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in ARCHIVE_EXTENSIONS


def gather_sources(src: Path, out: Path) -> list[Path]:
    return [
        path
        for path in sorted(src.iterdir())
        if path.name not in JUNK and not path.name.startswith((".", "_")) and path != out
    ]


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

    failed: set[str] = set()
    for std_id, items in sorted(by_student.items()):
        known = items[0][1]
        folder = out / roster_mod.folder_name(subject, submission_type, std_id)
        if folder.exists():
            shutil.rmtree(folder)
        multiple = len(items) > 1

        for source, _ in items:
            target = folder / source.stem if multiple else folder
            if not is_archive(source):
                if source.is_dir():
                    copy_into(content_root(source), target)
                else:
                    target.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target / source.name)
                continue
            staging = Path(tempfile.mkdtemp(prefix="get-fsa-training-done-extract-"))
            try:
                extracted, info = extract(source, staging)
                if extracted:
                    copy_into(content_root(staging), target)
                else:
                    outcome.failures.append((source.name, info))
                    failed.add(std_id)
            finally:
                shutil.rmtree(staging, ignore_errors=True)

        if folder.exists():
            outcome.created.append((std_id, known, multiple))

    # A failed extraction is its own line in the report; listing the trainee
    # under "did not submit" as well would say something untrue.
    accounted = {std_id for std_id, known, _ in outcome.created if known} | failed
    outcome.missing = [
        (trainee.std_id, trainee.name)
        for trainee in roster.active
        if trainee.std_id not in accounted
    ]
    return outcome
