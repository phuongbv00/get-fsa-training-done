"""`gftd install --cloud` — let cloud agents use a project's skill.

A cloud agent — Claude Code on the web, Codex cloud, the GitHub Copilot coding
agent — works in a fresh container that holds a clone of the repository and
nothing else. It finds the skill only when the project-scope install is
committed, and it finds the CLI only when something installs it there. That
something is `scripts/setup.sh` in the payload: it installs the CLI at the
payload's own version and builds the workers' environment.

This module wires the script into each host's setup step, where the host reads
one from the repository:

- Claude Code on the web: a SessionStart hook in `.claude/settings.json`,
  guarded by `CLAUDE_CODE_REMOTE` so a local session does nothing.
- GitHub Copilot coding agent: `.github/workflows/copilot-setup-steps.yml`.
- Codex cloud reads its setup script from the environment's settings, not the
  repository, so the line to paste there is printed instead.

Nothing a user wrote is overwritten: the hook is added next to theirs, and a
setup-steps workflow that already exists is left alone with the step to add
printed. `uninstall` takes back exactly what was added — the hook entry, and
the workflow only while it is still the one written here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..platforms.base import UNIVERSAL_PROJECT_SUBDIR

SETTINGS = Path(".claude/settings.json")
COPILOT_WORKFLOW = Path(".github/workflows/copilot-setup-steps.yml")


def setup_script(name: str) -> str:
    """The script's path from the project root, as a cloud agent's checkout has it."""
    return f"{UNIVERSAL_PROJECT_SUBDIR}/{name}/scripts/setup.sh"


def claude_hook_command(name: str) -> str:
    return f'[ "$CLAUDE_CODE_REMOTE" != true ] || sh "$CLAUDE_PROJECT_DIR/{setup_script(name)}"'


def copilot_workflow(name: str) -> str:
    return f"""\
# Prepares the GitHub Copilot coding agent's environment before it starts work.
# Written by `gftd install --cloud`: it installs the CLI the {name}
# skill calls, at the skill's own version. `gftd uninstall` removes this file
# while it is unchanged.
name: Copilot Setup Steps

on:
  workflow_dispatch:
  push:
    paths: [{COPILOT_WORKFLOW.as_posix()}]
  pull_request:
    paths: [{COPILOT_WORKFLOW.as_posix()}]

jobs:
  copilot-setup-steps:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - name: Install the {name} CLI
        run: sh {setup_script(name)}
"""


@dataclass
class Change:
    """One file this module writes or takes back, and what happens to it."""

    path: Path
    action: str  # "add", "present", "skip" or "remove"
    detail: str = ""


# ------------------------------------------------------------------- Claude Code


def _read_settings(path: Path) -> dict | None:
    """The settings as a dict; `{}` when absent, None when unreadable."""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_settings(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _is_ours(hook: object, name: str) -> bool:
    return isinstance(hook, dict) and setup_script(name) in str(hook.get("command", ""))


def _session_start(data: dict) -> list | None:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return None
    entries = hooks.get("SessionStart")
    return entries if isinstance(entries, list) else None


def _has_hook(data: dict, name: str) -> bool:
    for entry in _session_start(data) or []:
        if isinstance(entry, dict) and any(_is_ours(h, name) for h in entry.get("hooks", [])):
            return True
    return False


def _add_claude(root: Path, name: str, *, dry_run: bool) -> Change:
    path = root / SETTINGS
    data = _read_settings(path)
    if data is None:
        return Change(path, "skip", "not a JSON object; add the SessionStart hook by hand")
    if _has_hook(data, name):
        return Change(path, "present")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict) or not isinstance(hooks.setdefault("SessionStart", []), list):
        return Change(path, "skip", "its hooks are not in the shape Claude Code reads")
    hooks["SessionStart"].append(
        {"hooks": [{"type": "command", "command": claude_hook_command(name)}]}
    )
    if not dry_run:
        _write_settings(path, data)
    return Change(path, "add", "SessionStart hook")


def _remove_claude(root: Path, name: str, *, dry_run: bool) -> Change | None:
    path = root / SETTINGS
    data = _read_settings(path)
    if not data or not _has_hook(data, name):
        return None
    entries = _session_start(data) or []
    kept = []
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("hooks"), list):
            entry["hooks"] = [h for h in entry["hooks"] if not _is_ours(h, name)]
            if not entry["hooks"]:
                continue
        kept.append(entry)
    hooks = data["hooks"]
    if kept:
        hooks["SessionStart"] = kept
    else:
        del hooks["SessionStart"]
        if not hooks:
            del data["hooks"]
    if not dry_run:
        if data:
            _write_settings(path, data)
        else:
            path.unlink()
    return Change(path, "remove", "SessionStart hook")


# ---------------------------------------------------------------- GitHub Copilot


def _add_copilot(root: Path, name: str, *, dry_run: bool) -> Change:
    path = root / COPILOT_WORKFLOW
    if path.is_file():
        if setup_script(name) in path.read_text(encoding="utf-8", errors="replace"):
            return Change(path, "present")
        return Change(
            path,
            "skip",
            f"it is yours; add a step running `sh {setup_script(name)}` "
            "after one setting up Python 3.12+",
        )
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(copilot_workflow(name), encoding="utf-8", newline="\n")
    return Change(path, "add", "Copilot setup steps")


def _remove_copilot(root: Path, name: str, *, dry_run: bool) -> Change | None:
    path = root / COPILOT_WORKFLOW
    if not path.is_file() or path.read_text(encoding="utf-8") != copilot_workflow(name):
        return None
    if not dry_run:
        path.unlink()
    return Change(path, "remove", "Copilot setup steps")


# ----------------------------------------------------------------------- entry points


def setup(root: Path, name: str, *, dry_run: bool = False) -> list[Change]:
    """Wire `setup.sh` into each host's setup step under `root`."""
    return [_add_claude(root, name, dry_run=dry_run), _add_copilot(root, name, dry_run=dry_run)]


def teardown(root: Path, name: str, *, dry_run: bool = False) -> list[Change]:
    """Take back what `setup` added under `root`, and nothing else."""
    changes = [_remove_claude(root, name, dry_run=dry_run)]
    changes.append(_remove_copilot(root, name, dry_run=dry_run))
    return [c for c in changes if c is not None]


def report(root: Path, name: str, changes: list[Change], *, dry_run: bool = False) -> None:
    """Say what was wired, and what is left for the user to do."""
    verb = {
        "add": "would add" if dry_run else "added",
        "present": "already has",
        "skip": "left alone",
    }
    for change in changes:
        where = _rel(change.path, root)
        if change.action == "present":
            print(f"cloud: {where} already runs {setup_script(name)}")
        elif change.action == "skip":
            print(f"cloud: {where} {verb['skip']}: {change.detail}")
        else:
            print(f"cloud: {verb[change.action]} {change.detail} in {where}")
    print(f"cloud: for Codex cloud, set the environment's setup script to: sh {setup_script(name)}")
    if not dry_run:
        paths = [UNIVERSAL_PROJECT_SUBDIR, ".claude", ".github"]
        print(f"cloud: commit {', '.join(paths)} so a cloud agent's checkout has them")


def report_teardown(root: Path, changes: list[Change], *, dry_run: bool = False) -> None:
    verb = "would remove" if dry_run else "removed"
    for change in changes:
        print(f"cloud: {verb} the {change.detail} in {_rel(change.path, root)}")


def _rel(path: Path, root: Path) -> str:
    try:
        return "./" + path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


__all__ = [
    "COPILOT_WORKFLOW",
    "SETTINGS",
    "Change",
    "claude_hook_command",
    "copilot_workflow",
    "report",
    "report_teardown",
    "setup",
    "setup_script",
    "teardown",
]
