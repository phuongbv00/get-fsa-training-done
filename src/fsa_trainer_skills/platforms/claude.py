"""Claude Code.

User scope is `${CLAUDE_CONFIG_DIR:-~/.claude}/skills/<name>`; project scope is
`<root>/.claude/skills/<name>`. Claude accepts frontmatter keys Codex rejects
(`user-invocable`, for one) and does not restrict subdirectory names, so its
validation is a strict subset of Codex's — we run Codex's rules here too rather
than maintaining a second, laxer checker that would let a Codex-invalid payload
through whenever someone installs for Claude only.
"""

from __future__ import annotations

from pathlib import Path

from .base import Platform, Problem
from .codex import validate_payload


class Claude(Platform):
    def validate(self, payload_dir: Path) -> list[Problem]:
        return validate_payload(payload_dir)


CLAUDE = Claude(
    key="claude",
    label="Claude Code",
    home_env="CLAUDE_CONFIG_DIR",
    home_default=".claude",
    skills_subdir="skills",
    project_subdir=".claude/skills",
    project_scope_verified=True,
)
