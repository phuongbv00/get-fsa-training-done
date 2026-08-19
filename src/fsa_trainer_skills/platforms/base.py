"""Platform abstraction: where a skill goes, and what a valid payload looks like."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

SCOPES = ("user", "project")


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

    def validate(self, payload_dir: Path) -> list[Problem]:  # pragma: no cover - overridden
        return []
