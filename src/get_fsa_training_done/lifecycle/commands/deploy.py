"""One real copy in `.agents/skills`, and a symlink for every agent that needs one.

The skill is written once per scope, to `~/.agents/skills/<name>` or
`<project>/.agents/skills/<name>`. Codex and GitHub Copilot read that folder
directly at both scopes and Antigravity at project scope; every other agent —
Claude Code, Antigravity at user scope — gets a symlink to it. An update
rewrites the one copy, so every agent sees the same version.

A copy is still written where a link cannot go: when the OS refuses symlinks
(Windows without Developer Mode), when an earlier release left a copy there
that the user has since edited, or when `--force` adopts a folder this CLI
did not create. Nothing here removes a real directory it did not record.

`plan` looks without touching anything, so the summary shown before the
question is exactly what `deploy` then does.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from ...__about__ import __version__
from ...errors import GftdError, UnmanagedDestinationError
from ...skill import Skill
from .. import prompt
from ..install import fsops, links, migrations, planner, removal
from ..install import receipt as receipt_mod
from ..install.planner import Action, Plan
from ..platforms import registry
from ..platforms.base import Platform, universal_root
from .common import format_dest, print_plan, short_dest, warn_unverified_scope

#: What happens at an agent's own skills folder.
LINK = "link"  # a new symlink into the shared copy
LINKED = "linked"  # already a symlink into it
REPLACE = "replace"  # an earlier release's copy, untouched since: becomes a link
KEEP_COPY = "keep-copy"  # an earlier release's copy the user edited: updated in place
ADOPT = "adopt"  # a folder this CLI did not write, taken over as a copy (--force)
BLOCKED = "blocked"  # a folder this CLI did not write, left alone
COPY = "copy"  # symlinks are not available here

LINK_ACTIONS = (LINK, LINKED, REPLACE)
COPY_ACTIONS = (KEEP_COPY, ADOPT, COPY)


@dataclass
class AgentDir:
    platform: Platform
    path: Path
    action: str


@dataclass
class Deployment:
    scope: str
    name: str
    shared: Path
    readers: list[Platform]
    dirs: list[AgentDir]
    #: Agents nobody picked that read the shared copy anyway.
    bystanders: list[Platform]
    #: Installs an earlier release left where these agents no longer look.
    legacy: list[tuple[Platform, Path]]
    existing: receipt_mod.Receipt | None
    unmanaged: bool
    project_root: Path | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def needs_shared(self) -> bool:
        return bool(self.readers) or any(d.action in LINK_ACTIONS for d in self.dirs)

    @property
    def agents(self) -> list[Platform]:
        linked = [d.platform for d in self.dirs if d.action in LINK_ACTIONS]
        return [*self.readers, *linked]


def plan(
    platforms: list[Platform],
    scope: str,
    name: str,
    project_root: Path | None,
    *,
    force: bool = False,
) -> Deployment:
    """Work out where the copy and the links go, without touching anything."""
    platforms = [p for p in platforms if scope == "user" or p.project_subdir]
    shared = universal_root(scope, project_root) / name
    can_link = links.supported()

    readers = [p for p in platforms if p.reads_universal(scope, project_root)]
    dirs = [
        AgentDir(p, p.dest(scope, name, project_root), "") for p in platforms if p not in readers
    ]
    for entry in dirs:
        entry.action = _classify(entry.path, shared, can_link=can_link, force=force)

    bystanders = [
        p
        for p in registry.resolve(registry.ALL)
        if p not in platforms and p.reads_universal(scope, project_root)
    ]
    legacy = [
        (p, path)
        for p in platforms
        for path in p.legacy_dests(scope, name, project_root)
        if not path.is_symlink()
        and receipt_mod.read(path) is not None
        and path.resolve() != shared.resolve()
    ]
    existing = receipt_mod.read(shared)
    unmanaged = (
        existing is None and shared.is_dir() and not shared.is_symlink() and any(shared.iterdir())
    )
    return Deployment(
        scope=scope,
        name=name,
        shared=shared,
        readers=readers,
        dirs=dirs,
        bystanders=bystanders,
        legacy=legacy,
        existing=existing,
        unmanaged=unmanaged,
        project_root=project_root,
    )


def _classify(path: Path, shared: Path, *, can_link: bool, force: bool) -> str:
    if not can_link:
        return COPY
    if links.points_to(path, shared):
        return LINKED
    if path.is_symlink() or not path.exists():
        return LINK
    if not path.is_dir() or not any(path.iterdir()):
        return LINK
    receipt = receipt_mod.read(path)
    if receipt is None:
        return ADOPT if force else BLOCKED
    return KEEP_COPY if _user_files(path, receipt) else REPLACE


def _user_files(dest: Path, receipt: receipt_mod.Receipt) -> list[str]:
    """Files in an install that are not ours untouched: edited, or added by the user."""
    to_delete, edited = removal.classify_recorded(dest, receipt)
    ours = {*to_delete, *edited, receipt_mod.RECEIPT_NAME}
    added = [p.as_posix() for p in fsops.walk_files(dest) if p.as_posix() not in ours]
    return [*edited, *added]


# ------------------------------------------------------------------------ summary


def summary(dep: Deployment) -> list[str]:
    """The lines of the "Installation Summary" box."""

    def names(platforms: list[Platform]) -> str:
        return prompt.selected_summary([p.label for p in platforms])

    def label(text: str, code: str) -> str:
        return prompt.paint(text, code)

    lines: list[str] = []
    if dep.needs_shared:
        lines.append(label(short_dest(dep.shared, dep.scope), "36"))
        if dep.readers:
            lines.append(f"  {label('universal:', '32')} {names(dep.readers)}")
        linked = [d.platform for d in dep.dirs if d.action in LINK_ACTIONS]
        if linked:
            lines.append(f"  symlink → {names(linked)}")
        if dep.bystanders:
            lines.append(label(f"  also read by: {names(dep.bystanders)}", "2"))
        if dep.unmanaged:
            lines.append(
                f"  {label('blocked:', '31')} not installed by this CLI (--force replaces it)"
            )
        elif dep.existing is not None and dep.existing.version != __version__:
            lines.append(f"  {label('updates:', '33')} {dep.existing.version} → {__version__}")
        elif dep.existing is not None:
            lines.append(label(f"  already at {__version__}", "2"))
        replaced = [d.platform for d in dep.dirs if d.action == REPLACE]
        if replaced:
            lines.append(f"  {label('overwrites:', '33')} {names(replaced)} (earlier copy)")

    for entry in dep.dirs:
        if entry.action in LINK_ACTIONS:
            continue
        where = short_dest(entry.path, dep.scope)
        if entry.action == BLOCKED:
            lines.append(f"{label(where, '36')}")
            lines.append(
                f"  {label('blocked:', '31')} {entry.platform.label} — not installed by "
                "this CLI (--force takes it over)"
            )
            continue
        why = {
            KEEP_COPY: "copy kept: you edited files in it",
            ADOPT: "copy: taken over with --force",
            COPY: "copy: this system cannot make symlinks",
        }[entry.action]
        lines.append(label(where, "36"))
        lines.append(f"  {entry.platform.label} — {why}")

    for platform, path in dep.legacy:
        lines.append(
            f"  {label('moves from:', '33')} {short_dest(path, dep.scope)} ({platform.label})"
        )
    return lines


# ---------------------------------------------------------------------- deploying


def deploy(skill: Skill, dep: Deployment, args: argparse.Namespace) -> int:
    """Write the shared copy, make the links, retire legacy installs. Returns failures."""
    failures = 0
    payload = skill.payload_dir
    for platform in [*dep.readers, *(d.platform for d in dep.dirs)]:
        if dep.scope == "project":
            warn_unverified_scope(platform, dep.scope)

    made: list[Path] = []
    if dep.needs_shared:
        keys = [p.key for p in dep.agents]
        try:
            install_copy(skill, dep.name, "shared copy", dep.scope, dep.shared, args, payload, keys)
        except GftdError as exc:
            _report(skill, "shared copy", dep.scope, exc)
            # Every link would point at a copy that is not ours.
            return 1 + sum(1 for d in dep.dirs if d.action in LINK_ACTIONS)

    for entry in dep.dirs:
        try:
            if _place(skill, dep, entry, args):
                made.append(entry.path)
        except GftdError as exc:
            failures += 1
            _report(skill, entry.platform.label, dep.scope, exc)

    if dep.needs_shared and not args.dry_run:
        _record_links(dep, made)

    for platform, path in dep.legacy:
        _retire(skill, platform, dep.scope, path, args)
    return failures


def _place(skill: Skill, dep: Deployment, entry: AgentDir, args: argparse.Namespace) -> bool:
    """Link or copy the skill into one agent's folder. True when a link now exists."""
    label = f"{skill.name}: {entry.platform.label} ({dep.scope})"
    where = format_dest(entry.path)
    target = format_dest(dep.shared)
    payload = skill.payload_dir
    keys = [entry.platform.key]

    if entry.action == BLOCKED:
        raise UnmanagedDestinationError(
            f"{entry.path} already exists and was not installed by get-fsa-training-done",
            hint="pass --force to adopt and overwrite it, or --name to install under another name",
        )
    if entry.action in COPY_ACTIONS:
        force = args.force or entry.action == ADOPT
        install_copy(
            skill,
            dep.name,
            entry.platform.label,
            dep.scope,
            entry.path,
            args,
            payload,
            keys,
            force=force,
        )
        return False
    if entry.action == LINKED:
        if args.verbose:
            print(f"{label}: already linked {where} -> {target}")
        return True
    if args.dry_run:
        verb = (
            "would replace the earlier copy with a link"
            if entry.action == REPLACE
            else "would link"
        )
        print(f"{label}: {verb} {where} -> {target}")
        return False
    if entry.action == REPLACE:
        receipt = receipt_mod.read(entry.path)
        if receipt is not None:
            removal.remove_recorded(entry.path, receipt)
    try:
        links.make(entry.path, dep.shared)
    except OSError as exc:
        print(f"{label}: could not create a symlink ({exc.strerror or exc}); copying instead")
        install_copy(
            skill, dep.name, entry.platform.label, dep.scope, entry.path, args, payload, keys
        )
        return False
    print(f"{label}: linked {where} -> {target}")
    return True


def _record_links(dep: Deployment, made: list[Path]) -> None:
    """Remember every symlink into the shared copy, so uninstall can find them."""
    receipt = receipt_mod.read(dep.shared)
    if receipt is None:
        return
    known = [Path(p) for p in receipt.links if links.points_to(Path(p), dep.shared)]
    paths = sorted({str(p) for p in [*known, *made]})
    keys = list(dict.fromkeys([*receipt.agent_keys(), *(p.key for p in dep.agents)]))
    if paths != receipt.links or keys != receipt.agents:
        receipt.links = paths
        receipt.agents = keys
        receipt_mod.write(dep.shared, receipt)


def _retire(
    skill: Skill, platform: Platform, scope: str, path: Path, args: argparse.Namespace
) -> None:
    """Remove what an earlier release installed where this agent no longer looks."""
    label = f"{skill.name}: {platform.label} ({scope})"
    if args.dry_run:
        print(f"{label}: would remove the earlier install at {format_dest(path)}")
        return
    receipt = receipt_mod.read(path)
    if receipt is None:
        return
    _, leftovers = removal.remove_recorded(path, receipt)
    print(f"{label}: removed the earlier install at {format_dest(path)}")
    for rel in leftovers[:10]:
        print(f"    kept {rel.as_posix()} (edited or added by you)")


def _report(skill: Skill, who: str, scope: str, exc: GftdError) -> None:
    print(f"ERROR: {skill.name}: {who} ({scope}): {exc.message}")
    if exc.hint:
        print(f"       {exc.hint}")


# ---------------------------------------------------------------------- finding


@dataclass
class Found:
    """One real install on disk: the folder holding our receipt, and what points at it."""

    scope: str
    dest: Path
    receipt: receipt_mod.Receipt
    agents: list[Platform] = field(default_factory=list)
    links: list[tuple[Platform | None, Path]] = field(default_factory=list)
    #: The agents for which this is where an earlier release installed.
    legacy_for: list[Platform] = field(default_factory=list)
    #: Whether this is the `.agents/skills` copy rather than one agent's own.
    shared: bool = False


def discover(name: str, scopes: tuple[str, ...], project_root: Path | None) -> list[Found]:
    """Every install of `name` this CLI made, across agents and scopes.

    The shared copy, each agent's own folder and each earlier release's
    location are looked at; a symlink is filed under the install it points to.
    Run from the folder that holds the user-scope config — the home directory,
    usually — and user and project scope name the same folder; it is one install.
    """
    platforms = registry.resolve(registry.ALL)
    by_path: dict[Path, Found] = {}

    def found_at(path: Path, scope: str) -> Found | None:
        real = path.resolve()
        if real in by_path:
            return by_path[real]
        receipt = receipt_mod.read(real)
        if receipt is None:
            return None
        keys = receipt.agent_keys()
        agents = [p for p in platforms if p.key in keys]
        shared = real == (universal_root(scope, project_root) / name).resolve()
        by_path[real] = Found(scope, real, receipt, agents, shared=shared)
        return by_path[real]

    for scope in scopes:
        candidates: list[tuple[Platform | None, Path, bool]] = [
            (None, universal_root(scope, project_root) / name, False)
        ]
        for p in platforms:
            if scope == "project" and not p.project_subdir:
                continue
            candidates.append((p, p.dest(scope, name, project_root), False))
            candidates += [(p, d, True) for d in p.legacy_dests(scope, name, project_root)]

        for owner, path, legacy in candidates:
            try:
                if not path.exists():
                    continue
            except OSError:
                continue
            found = found_at(path, scope)
            if found is None:
                continue
            if path.is_symlink():
                if all(link != path for _, link in found.links):
                    found.links.append((owner, path))
                if owner is not None and owner not in found.agents:
                    found.agents.append(owner)
            elif legacy and owner is not None and owner not in found.legacy_for:
                found.legacy_for.append(owner)

    for found in by_path.values():
        for raw in found.receipt.links:
            link = Path(raw)
            if links.points_to(link, found.dest) and all(p != link for _, p in found.links):
                found.links.append((None, link))
    return list(by_path.values())


# --------------------------------------------------------------- writing a copy


def install_copy(
    skill: Skill,
    name: str,
    who: str,
    scope: str,
    dest: Path,
    args: argparse.Namespace,
    payload: Path,
    agents: list[str],
    *,
    force: bool | None = None,
) -> None:
    """Write (or bring up to date) one real copy of the payload at `dest`."""
    force = args.force if force is None else force
    label = f"{skill.name}: {who} ({scope})"

    existing = receipt_mod.read(dest)
    if existing is None and dest.exists() and any(dest.iterdir()) and not force:
        raise UnmanagedDestinationError(
            f"{dest} already exists and was not installed by get-fsa-training-done",
            hint="pass --force to adopt and overwrite it, or --name to install under another name",
        )
    if existing is not None and existing.skill_name and existing.skill_name != name:
        raise UnmanagedDestinationError(
            f"{dest} holds the skill {existing.skill_name!r}, not {name!r}"
        )

    plan_ = planner.build_plan(dest, payload, existing, __version__)
    keys = list(dict.fromkeys([*(existing.agent_keys() if existing else []), *agents]))

    if existing is not None and existing.version == __version__ and not plan_.changed:
        print(f"{label}: already installed at {__version__} — {dest}")
        if not args.dry_run and keys != existing.agents:
            existing.agents = keys
            receipt_mod.write(dest, existing)
        return

    if args.dry_run:
        verb = "would install" if existing is None else "would update"
        print(f"{label}: {verb} {name} {__version__} -> {dest}")
        print_plan(plan_, verbose=args.verbose)
        return

    apply_plan(dest, payload, plan_, force=force)
    notes = migrations.run_all(dest, existing.version) if existing else []

    receipt_mod.write(
        dest,
        receipt_mod.Receipt(
            version=__version__,
            skill_name=name,
            platform=agents[0] if len(agents) == 1 else "shared",
            scope=scope,
            dest=str(dest),
            installed_at=receipt_mod.utc_now(),
            installed_by=receipt_mod.installed_by(),
            cli=receipt_mod.cli_invocation(),
            dirs=plan_.dirs,
            files=_file_records(dest, plan_, force=force),
            venv=(existing.venv if existing and existing.venv else str(_venv_hint(skill))),
            agents=keys,
            links=existing.links if existing else [],
        ),
    )

    verb = "installed" if existing is None else f"updated {existing.version} ->"
    print(f"{label}: {verb} {__version__} at {dest}")
    print_plan(plan_, verbose=args.verbose)
    for note in notes:
        print(f"  migration: {note}")
    _report_conflicts(plan_, force=force)


def apply_plan(dest: Path, payload: Path, plan: Plan, *, force: bool) -> None:
    """Write the payload into `dest` via a staged swap."""
    preserved = planner.preserved_paths(dest, plan) if dest.exists() else []
    conflicts = {e.path for e in plan.conflicts}

    def build(staging: Path) -> None:
        for entry in plan.entries:
            if entry.action is Action.REMOVE:
                continue
            if not entry.payload_hash:
                continue
            src = payload / entry.path
            dst = staging / entry.path
            if entry.action is Action.CONFLICT and not force:
                # Keep the user's file; drop ours next to it for comparison.
                fsops.copy_file(dest / entry.path, dst)
                fsops.copy_file(src, staging / (entry.path + ".new"))
                continue
            if entry.action is Action.CONFLICT and force:
                fsops.copy_file(dest / entry.path, staging / (entry.path + ".bak"))
            fsops.copy_file(src, dst)

        for rel in preserved:
            if rel in conflicts:
                continue
            source = dest / rel
            if source.is_file():
                fsops.copy_file(source, staging / rel)

        for rel in plan.dirs:
            (staging / rel).mkdir(parents=True, exist_ok=True)

    fsops.staged_swap(dest, build)


def _file_records(dest: Path, plan: Plan, *, force: bool) -> list[receipt_mod.FileRecord]:
    """Record only the files we actually own.

    A conflict we chose not to overwrite is the user's file sitting at our path.
    Claiming it in the receipt would mean `uninstall` deletes their content, and
    the next `update` would stop noticing the conflict. So we leave it out: it
    stays theirs, and it keeps being reported as a conflict until they resolve
    it or pass --force.
    """
    records = []
    for entry in plan.entries:
        if not entry.payload_hash or entry.action is Action.REMOVE:
            continue
        if entry.action is Action.CONFLICT and not force:
            continue
        path = dest / entry.path
        if not path.is_file():
            continue
        stat = path.stat()
        records.append(
            receipt_mod.FileRecord(
                path=entry.path,
                sha256=fsops.sha256_file(path),
                bytes=stat.st_size,
                mode=oct(stat.st_mode & 0o777)[2:].rjust(4, "0"),
            )
        )
    return records


def _report_conflicts(plan: Plan, *, force: bool) -> None:
    conflicts = plan.conflicts
    if not conflicts:
        return
    if force:
        print(f"  {len(conflicts)} modified file(s) overwritten; previous bytes kept as *.bak")
        return
    print(f"  {len(conflicts)} file(s) you had modified were left as-is:")
    for entry in conflicts:
        print(f"    {entry.path}  (new version written to {entry.path}.new)")
    print("  re-run with --force to take the shipped version instead")


def _venv_hint(skill: Skill) -> Path:
    from ..envmgr import stamp

    return stamp.venv_path((skill.dep_group,))


__all__ = [
    "Deployment",
    "Found",
    "apply_plan",
    "deploy",
    "discover",
    "install_copy",
    "plan",
    "summary",
]
