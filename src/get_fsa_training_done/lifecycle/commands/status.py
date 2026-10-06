"""`get-fsa-training-done status` — where the skill is installed, and whether it drifted."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ...__about__ import __version__
from ...skill import SKILL, Skill
from ..install import fsops, planner
from ..install import receipt as receipt_mod
from ..platforms import registry
from .common import format_dest


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "status",
        help="list installs found in the known skill directories",
    )
    parser.add_argument("--platform", default=registry.ALL, help="limit to one host")
    parser.add_argument("--name", default=None, help="override the installed directory name")
    parser.add_argument("--project-root", default=None, help="project root for project scope")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    skill = SKILL
    name = args.name or skill.name
    project_root = Path(args.project_root).expanduser().resolve() if args.project_root else None

    rows = []
    for platform in registry.resolve(args.platform):
        # Run from the directory that *holds* the user-scope config — your
        # home directory, usually — and `<cwd>/.claude/skills` is the very
        # same folder as `~/.claude/skills`. There is one install there, so
        # report it once, under the scope we looked at first.
        seen: set[Path] = set()
        for scope in ("user", "project"):
            if scope == "project" and not platform.project_subdir:
                continue
            dest = platform.dest(scope, name, project_root)
            if not dest.exists():
                continue
            resolved = dest.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            rows.append(_describe(skill, platform.key, platform.label, scope, dest))

    if args.as_json:
        print(json.dumps({"package_version": __version__, "installs": rows}, indent=2))
        return 0

    print(f"package {__version__}")
    print(f"\n{skill.name}")
    if not rows:
        print("  No installs found.")
        print("\nRun `get-fsa-training-done install --platform all` to install.")
        return 0
    for row in rows:
        marker = "  " if row["current"] else "! "
        line = f"{row['label']} ({row['scope']}): {row['version']}  {row['dest_display']}"
        print(f"{marker}  {line}")
        if row["drift"]:
            print(f"      {row['drift']} file(s) differ from what was installed")
        if not row["current"] and row["version"] != "unmanaged":
            print(f"      update available: {__version__}  (run `get-fsa-training-done update`)")
        if row["version"] == "unmanaged":
            print("      no receipt — not installed by get-fsa-training-done")
    return 0


def _describe(skill: Skill, key: str, label: str, scope: str, dest: Path) -> dict:
    receipt = receipt_mod.read(dest)
    if receipt is None:
        return {
            "skill": skill.name,
            "platform": key,
            "label": label,
            "scope": scope,
            "dest": str(dest),
            "dest_display": format_dest(dest),
            "version": "unmanaged",
            "current": False,
            "drift": 0,
        }

    drift = 0
    for record in receipt.files:
        path = dest / record.path
        if not path.is_file() or fsops.sha256_file(path) != record.sha256:
            drift += 1

    plan_changed = planner.build_plan(dest, skill.payload_dir, receipt, __version__).changed

    return {
        "skill": skill.name,
        "platform": key,
        "label": label,
        "scope": scope,
        "dest": str(dest),
        "dest_display": format_dest(dest),
        "version": receipt.version,
        "installed_at": receipt.installed_at,
        "current": receipt.version == __version__ and not plan_changed,
        "drift": drift,
    }
