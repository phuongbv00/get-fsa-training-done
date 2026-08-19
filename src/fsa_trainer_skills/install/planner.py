"""Work out what an install/update would change, before changing anything.

Every path is classified by comparing three hashes: what the payload ships,
what the receipt says we wrote last time, and what is actually on disk. The
interesting case is CONFLICT — on-disk differs from the receipt, so the user
edited the file. We never overwrite that by default; the payload version is
written alongside as `<path>.new` and reported.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from . import fsops
from .receipt import RECEIPT_NAME, Receipt


class Action(Enum):
    KEEP = "keep"
    UPDATE = "update"
    ADD = "add"
    REMOVE = "remove"
    CONFLICT = "conflict"
    MISSING = "missing"


#: Ordering used when printing a plan, most-noteworthy first.
ACTION_ORDER = [
    Action.CONFLICT,
    Action.ADD,
    Action.UPDATE,
    Action.REMOVE,
    Action.MISSING,
    Action.KEEP,
]


@dataclass(frozen=True)
class Entry:
    path: str
    action: Action
    payload_hash: str = ""
    receipt_hash: str = ""
    disk_hash: str = ""


@dataclass
class Plan:
    dest: Path
    entries: list[Entry]
    dirs: list[str]
    old_version: str | None
    new_version: str

    def by_action(self, action: Action) -> list[Entry]:
        return [e for e in self.entries if e.action is action]

    @property
    def conflicts(self) -> list[Entry]:
        return self.by_action(Action.CONFLICT)

    @property
    def changed(self) -> bool:
        return any(e.action is not Action.KEEP for e in self.entries)

    def counts(self) -> dict[Action, int]:
        counts = {action: 0 for action in Action}
        for entry in self.entries:
            counts[entry.action] += 1
        return counts

    def summary(self) -> str:
        counts = self.counts()
        parts = [
            f"{counts[a]} {a.value}" for a in ACTION_ORDER if counts[a] and a is not Action.KEEP
        ]
        parts.append(f"{counts[Action.KEEP]} unchanged")
        return ", ".join(parts)


def build_plan(
    dest: Path,
    payload_dir: Path,
    receipt: Receipt | None,
    new_version: str,
) -> Plan:
    payload_files = {p.as_posix(): payload_dir / p for p in fsops.walk_files(payload_dir)}
    payload_hashes = {rel: fsops.sha256_file(src) for rel, src in payload_files.items()}
    receipt_hashes = receipt.file_hashes() if receipt else {}

    entries: list[Entry] = []
    for rel in sorted(set(payload_hashes) | set(receipt_hashes)):
        on_disk = dest / rel
        disk_hash = fsops.sha256_file(on_disk) if on_disk.is_file() else ""
        payload_hash = payload_hashes.get(rel, "")
        receipt_hash = receipt_hashes.get(rel, "")

        if payload_hash and not receipt_hash:
            # New in this version. If a file is already sitting there and does
            # not match, that is the user's file, not ours.
            action = Action.ADD if disk_hash in ("", payload_hash) else Action.CONFLICT
        elif payload_hash and receipt_hash:
            if not disk_hash:
                action = Action.MISSING
            elif disk_hash != receipt_hash and disk_hash != payload_hash:
                action = Action.CONFLICT
            elif payload_hash == disk_hash:
                action = Action.KEEP
            else:
                action = Action.UPDATE
        else:
            # Dropped from the payload in this version.
            if not disk_hash:
                action = Action.KEEP
            elif disk_hash == receipt_hash:
                action = Action.REMOVE
            else:
                action = Action.CONFLICT

        entries.append(
            Entry(
                path=rel,
                action=action,
                payload_hash=payload_hash,
                receipt_hash=receipt_hash,
                disk_hash=disk_hash,
            )
        )

    return Plan(
        dest=dest,
        entries=entries,
        dirs=[p.as_posix() for p in fsops.walk_dirs(payload_dir)],
        old_version=receipt.version if receipt else None,
        new_version=new_version,
    )


def preserved_paths(dest: Path, plan: Plan) -> list[str]:
    """Files under `dest` that we must carry across a staged swap untouched.

    Anything the payload does not own: user-added files, previous `.new`/`.bak`
    sidecars, and the receipt itself (rewritten separately).
    """
    payload_owned = {
        e.path for e in plan.entries if e.action is not Action.REMOVE and e.payload_hash
    }
    keep: list[str] = []
    for rel in fsops.walk_files(dest):
        posix = rel.as_posix()
        if posix == RECEIPT_NAME or posix in payload_owned:
            continue
        entry = next((e for e in plan.entries if e.path == posix), None)
        if entry is not None and entry.action is Action.REMOVE:
            continue
        keep.append(posix)
    return keep
