"""Google Antigravity (the Antigravity app and IDE).

User scope is `~/.gemini/config/skills/<name>`, the global skills directory the
Antigravity docs give for both the app and the IDE. Project scope is
`<root>/.agents/skills/<name>`, the workspace default; Antigravity still reads
the older `<root>/.agent/skills` too. The Antigravity CLI keeps its global
skills elsewhere (`~/.gemini/antigravity-cli/skills`) and is not targeted.

Antigravity documents no environment variable that relocates `~/.gemini/config`.
`ANTIGRAVITY_HOME` is read by this CLI only, so tests and CI can point the user
scope at a throwaway directory; Antigravity itself ignores it. Neither scope has
been confirmed against a running Antigravity here, so project scope warns like
any other unverified one.

Antigravity requires only `description` in the frontmatter, so the Codex
validator is the binding one here too.
"""

from __future__ import annotations

from pathlib import Path

from .base import Platform, Problem
from .codex import validate_payload


class Antigravity(Platform):
    def validate(self, payload_dir: Path) -> list[Problem]:
        return validate_payload(payload_dir)


ANTIGRAVITY = Antigravity(
    key="antigravity",
    label="Antigravity",
    home_env="ANTIGRAVITY_HOME",
    home_default=".gemini/config",
    skills_subdir="skills",
    project_subdir=".agents/skills",
    project_aliases=(".agent/skills",),
)
