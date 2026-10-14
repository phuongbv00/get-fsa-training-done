"""`gftd status` — where the skill is installed, and whether it drifted.

It reads the same installs `update` and `uninstall` act on (`deploy.discover`)
and lists an agent only where the install's receipt names it, or a link of its
own points into it. Reading the agents' folders one by one instead would
report an agent that merely *can* see the shared `.agents/skills` copy — Copilot
next to a Codex install, or Antigravity at "project" scope when run from the
home directory, where the project's `.agents/skills` is the user-scope folder.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ...__about__ import __version__
from ...skill import SKILL, Skill
from .. import prompt
from ..install import fsops, planner
from ..install import receipt as receipt_mod
from ..platforms import registry
from ..platforms.base import Platform
from . import deploy
from .common import format_dest, short_dest

SCOPE_LABELS = {"user": "global", "project": "project"}


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "status",
        help="list where the skill is installed, for which agents",
    )
    parser.add_argument("--platform", default=registry.ALL, help="limit to one agent")
    parser.add_argument("--name", default=None, help="override the installed directory name")
    parser.add_argument("--project-root", default=None, help="project root for project scope")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    skill = SKILL
    name = args.name or skill.name
    project_root = Path(args.project_root).expanduser().resolve() if args.project_root else None
    wanted = {p.key for p in registry.resolve(args.platform)}

    rows = installs(skill, name, project_root)
    rows += unmanaged(skill, name, project_root, rows)
    rows = [row for row in rows if row["platform"] in wanted]

    if args.as_json:
        print(json.dumps({"package_version": __version__, "installs": rows}, indent=2))
        return 0

    print(f"package {__version__}")
    print(f"\n{skill.name}")
    if not rows:
        print("  No installs found.")
        print("\nRun `gftd install` to install.")
        return 0
    print()
    for line in table(rows):
        print(line)
    return 0


def installs(skill: Skill, name: str, project_root: Path | None) -> list[dict]:
    """One row per agent an install was made for."""
    rows = []
    for found in deploy.discover(name, ("user", "project"), project_root):
        state = _state(skill, found.dest, found.receipt)
        linked = {p: path for p, path in found.links if p is not None}
        for platform in _agents(found):
            path = linked.get(platform, found.dest)
            legacy = platform in found.legacy_for
            rows.append(_row(skill, platform, found.scope, path, found.receipt, state, legacy))
    return rows


def _agents(found: deploy.Found) -> list[Platform]:
    agents = list(found.agents)
    agents += [p for p in found.legacy_for if p not in agents]
    order = registry.names()
    return sorted(agents, key=lambda p: order.index(p.key))


def unmanaged(skill: Skill, name: str, project_root: Path | None, rows: list[dict]) -> list[dict]:
    """An agent's folder holding something of this name that this CLI did not write."""
    known = {Path(row["dest"]) for row in rows}
    out, seen = [], set()
    for platform in registry.resolve(registry.ALL):
        for scope in ("user", "project"):
            if scope == "project" and not platform.project_subdir:
                continue
            dest = platform.dest(scope, name, project_root)
            if dest in known or not dest.exists() or receipt_mod.read(dest) is not None:
                continue
            key = (platform.key, dest.resolve())
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "skill": skill.name,
                    "platform": platform.key,
                    "label": platform.label,
                    "scope": scope,
                    "dest": str(dest),
                    "dest_display": short_dest(dest, scope),
                    "link_to": "",
                    "version": "unmanaged",
                    "current": False,
                    "drift": 0,
                    "legacy": False,
                }
            )
    return out


def _state(skill: Skill, dest: Path, receipt: receipt_mod.Receipt) -> dict:
    drift = 0
    for record in receipt.files:
        path = dest / record.path
        if not path.is_file() or fsops.sha256_file(path) != record.sha256:
            drift += 1
    changed = planner.build_plan(dest, skill.payload_dir, receipt, __version__).changed
    return {"drift": drift, "current": receipt.version == __version__ and not changed}


def _row(
    skill: Skill,
    platform: Platform,
    scope: str,
    path: Path,
    receipt: receipt_mod.Receipt,
    state: dict,
    legacy: bool,
) -> dict:
    return {
        "skill": skill.name,
        "platform": platform.key,
        "label": platform.label,
        "scope": scope,
        "dest": str(path),
        "dest_display": short_dest(path, scope),
        "link_to": str(path.resolve()) if path.is_symlink() else "",
        "version": receipt.version,
        "installed_at": receipt.installed_at,
        "current": state["current"] and not legacy,
        "drift": state["drift"],
        "legacy": legacy,
    }


def table(rows: list[dict]) -> list[str]:
    """The installs as aligned columns: agent, scope, version, state, location."""
    header = ("Agent", "Scope", "Version", "State", "Location")
    body = []
    for row in rows:
        location = row["dest_display"]
        if row["link_to"]:
            location += f" → {format_dest(Path(row['link_to']))}"
        scope = SCOPE_LABELS.get(row["scope"], row["scope"])
        body.append((row["label"], scope, row["version"], _describe_state(row), location))
    widths = [max(len(cells[i]) for cells in [header, *body]) for i in range(len(header) - 1)]

    def line(cells: tuple[str, ...]) -> str:
        padded = [cell.ljust(width) for cell, width in zip(cells, widths, strict=False)]
        return "  " + "  ".join([*padded, cells[-1]])

    return [prompt.paint(line(header), "1"), *(line(cells) for cells in body)]


def _describe_state(row: dict) -> str:
    if row["version"] == "unmanaged":
        return "not installed by gftd"
    if row["legacy"]:
        return "old location: run gftd update"
    if row["version"] != __version__:
        return f"update to {__version__}: run gftd update"
    if row["drift"]:
        return f"{row['drift']} file(s) edited"
    if not row["current"]:
        return "out of step: run gftd update"
    return "up to date"
