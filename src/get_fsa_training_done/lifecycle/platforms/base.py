"""Platform abstraction: where a skill goes, and what a valid payload looks like."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

SCOPES = ("user", "project")

#: Relocates `~/.agents`, the user-scope universal skills folder. Read by this
#: CLI only (no agent documents a variable for it), so tests and CI can point it
#: at a throwaway directory.
AGENTS_HOME_ENV = "GET_FSA_TRAINING_DONE_AGENTS_HOME"
#: The universal skills folder under a project root, and under `~/.agents`.
UNIVERSAL_PROJECT_SUBDIR = ".agents/skills"


def universal_root(scope: str, project_root: Path | None = None) -> Path:
    """`.agents/skills` for `scope`: where the one real copy of a skill lives.

    Codex and GitHub Copilot read it at both scopes and Antigravity at project
    scope; every other agent gets a symlink into it.
    """
    if scope == "user":
        override = os.environ.get(AGENTS_HOME_ENV)
        home = Path(override).expanduser() if override else Path.home() / ".agents"
        return home / "skills"
    if scope == "project":
        return (project_root or Path.cwd()) / UNIVERSAL_PROJECT_SUBDIR
    raise ValueError(f"unknown scope: {scope!r}")


@dataclass(frozen=True)
class Problem:
    """A payload-validation finding. `fatal` blocks the install."""

    path: str
    message: str
    fatal: bool = True

    def __str__(self) -> str:
        return f"{'ERROR' if self.fatal else 'WARNING'}: {self.path}: {self.message}"


@dataclass(frozen=True)
class Platform:
    """A skill host (Claude Code, Codex, ...)."""

    key: str
    label: str
    #: Environment variable that relocates the user-scope config home, if any.
    home_env: str = ""
    #: Default user-scope config home relative to `~`.
    home_default: str = ""
    #: Directory under the config home that holds skills.
    skills_subdir: str = "skills"
    #: Directory under the project root that holds skills.
    project_subdir: str = ""
    #: Extra project-root-relative dirs this platform also reads, for messaging only.
    project_aliases: tuple[str, ...] = field(default_factory=tuple)
    #: Set when project scope is verified to work; otherwise install warns.
    project_scope_verified: bool = False
    #: Where earlier releases installed for user scope, as `(env var, default
    #: under ~)`; `update` moves an install found there and `uninstall` removes it.
    legacy_homes: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    #: Where earlier releases installed for project scope, under the project root.
    legacy_project_subdirs: tuple[str, ...] = field(default_factory=tuple)

    def home(self) -> Path:
        override = os.environ.get(self.home_env) if self.home_env else None
        if override:
            return Path(override).expanduser()
        return Path.home() / self.home_default

    def root(self, scope: str, project_root: Path | None = None) -> Path:
        """Directory that *contains* installed skills for this scope."""
        if scope == "user":
            return self.home() / self.skills_subdir
        if scope == "project":
            if not self.project_subdir:
                raise ValueError(f"{self.label} has no project scope")
            return (project_root or Path.cwd()) / self.project_subdir
        raise ValueError(f"unknown scope: {scope!r}")

    def dest(self, scope: str, name: str, project_root: Path | None = None) -> Path:
        return self.root(scope, project_root) / name

    def reads_universal(self, scope: str, project_root: Path | None = None) -> bool:
        """Whether this agent reads the shared `.agents/skills` copy directly."""
        if scope == "project" and not self.project_subdir:
            return False
        return self.root(scope, project_root) == universal_root(scope, project_root)

    def legacy_dests(self, scope: str, name: str, project_root: Path | None = None) -> list[Path]:
        """Where an earlier release of this CLI put the skill for this agent."""
        if scope == "user":
            roots = []
            for env, default in self.legacy_homes:
                override = os.environ.get(env)
                home = Path(override).expanduser() if override else Path.home() / default
                roots.append(home / self.skills_subdir)
        else:
            base = project_root or Path.cwd()
            roots = [base / subdir for subdir in self.legacy_project_subdirs]
        return [root / name for root in roots]

    def validate(self, payload_dir: Path) -> list[Problem]:  # pragma: no cover - overridden
        return []
