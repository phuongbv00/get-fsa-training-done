"""GitHub Copilot (Copilot CLI and agent mode in VS Code and Visual Studio).

GitHub's docs name `~/.copilot/skills` or `~/.agents/skills` for personal
skills and `.github/skills`, `.claude/skills` or `.agents/skills` in a
repository, so Copilot reads the shared `.agents/skills` copy directly at both
scopes and needs no copy or link of its own. Earlier releases of this CLI
wrote `$COPILOT_HOME/skills` (default `~/.copilot/skills`) and
`<root>/.github/skills`; they are listed as legacy so `update` moves an install
out of them instead of leaving Copilot to load the skill twice. Neither scope
has been confirmed against a running Copilot here, so project scope warns like
any other unverified one.

Copilot's own frontmatter rules are laxer than Codex's (it accepts uppercase,
dots and spaces in `name`, and extra keys such as `argument-hint`), so the
Codex validator is the binding one here too.
"""

from __future__ import annotations

from pathlib import Path

from .base import AGENTS_HOME_ENV, UNIVERSAL_PROJECT_SUBDIR, Platform, Problem
from .codex import validate_payload


class Copilot(Platform):
    def validate(self, payload_dir: Path) -> list[Problem]:
        return validate_payload(payload_dir)


COPILOT = Copilot(
    key="copilot",
    label="GitHub Copilot",
    home_env=AGENTS_HOME_ENV,
    home_default=".agents",
    skills_subdir="skills",
    project_subdir=UNIVERSAL_PROJECT_SUBDIR,
    legacy_homes=(("COPILOT_HOME", ".copilot"),),
    legacy_project_subdirs=(".github/skills",),
)
