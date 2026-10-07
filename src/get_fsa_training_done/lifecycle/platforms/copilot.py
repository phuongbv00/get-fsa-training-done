"""GitHub Copilot (Copilot CLI and agent mode in VS Code).

User scope is `$COPILOT_HOME/skills/<name>` (default `~/.copilot/skills`), the
personal-skills directory both the Copilot CLI and VS Code read. Project scope
is `<root>/.github/skills/<name>`, the location GitHub's docs name first; Copilot
also reads `.claude/skills` and `.agents/skills` in a repository. Neither scope
has been confirmed against a running Copilot here, so project scope warns like
any other unverified one.

Copilot's own frontmatter rules are laxer than Codex's (it accepts uppercase,
dots and spaces in `name`, and extra keys such as `argument-hint`), so the
Codex validator is the binding one here too.
"""

from __future__ import annotations

from pathlib import Path

from .base import Platform, Problem
from .codex import validate_payload


class Copilot(Platform):
    def validate(self, payload_dir: Path) -> list[Problem]:
        return validate_payload(payload_dir)


COPILOT = Copilot(
    key="copilot",
    label="GitHub Copilot",
    home_env="COPILOT_HOME",
    home_default=".copilot",
    skills_subdir="skills",
    project_subdir=".github/skills",
    project_aliases=(".claude/skills", ".agents/skills"),
)
