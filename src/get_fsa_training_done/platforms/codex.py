"""Codex CLI.

User scope is `$CODEX_HOME/skills/<name>` (default `~/.codex/skills`). Project
scope was verified empirically against codex-cli 0.147.0 with
`codex --cd <root> debug prompt-input`: a skill at `<root>/.codex/skills/<name>`
*and* one at `<root>/.agents/skills/<name>` both appear in the model-visible
skills list; a plain `<root>/skills/<name>` does not. We write `.codex/skills`
because it is unambiguous about which host it belongs to.

The validation rules below mirror Codex's own
`$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py` and
`init_skill.py`. They are the strictest of the platforms we target, so
`install` applies them regardless of `--platform`: one payload has to satisfy
every host, and it is cheaper to fail here than to ship something Codex drops.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..skillmeta import FrontmatterError, read_skill_frontmatter
from .base import Platform, Problem

ALLOWED_FRONTMATTER_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
ALLOWED_SUBDIRS = {"scripts", "references", "assets"}
NAME_RE = re.compile(r"^[a-z0-9-]+$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024


class Codex(Platform):
    def validate(self, payload_dir: Path) -> list[Problem]:
        return validate_payload(payload_dir)


def validate_payload(payload_dir: Path) -> list[Problem]:
    """Check a skill payload against Codex's rules. Empty list means valid."""
    problems: list[Problem] = []
    skill_md = payload_dir / "SKILL.md"
    if not skill_md.is_file():
        return [Problem("SKILL.md", "not found")]

    for entry in sorted(payload_dir.iterdir()):
        if entry.is_dir() and entry.name not in ALLOWED_SUBDIRS:
            problems.append(
                Problem(
                    entry.name + "/",
                    "not an allowed skill subdirectory; Codex reads only "
                    + ", ".join(sorted(ALLOWED_SUBDIRS)),
                )
            )

    try:
        front = read_skill_frontmatter(skill_md)
    except FrontmatterError as exc:
        return problems + [Problem("SKILL.md", str(exc))]

    unexpected = set(front) - ALLOWED_FRONTMATTER_KEYS
    if unexpected:
        problems.append(
            Problem(
                "SKILL.md",
                "unexpected frontmatter key(s): "
                + ", ".join(sorted(unexpected))
                + "; allowed are "
                + ", ".join(sorted(ALLOWED_FRONTMATTER_KEYS)),
            )
        )

    name = front.get("name")
    if not isinstance(name, str) or not name.strip():
        problems.append(Problem("SKILL.md", "missing 'name' in frontmatter"))
    else:
        name = name.strip()
        if not NAME_RE.match(name):
            problems.append(
                Problem("SKILL.md", f"name {name!r} must be lowercase letters, digits and hyphens")
            )
        elif name.startswith("-") or name.endswith("-") or "--" in name:
            problems.append(
                Problem(
                    "SKILL.md",
                    f"name {name!r} cannot start or end with a hyphen or contain '--'",
                )
            )
        if len(name) > MAX_NAME_LENGTH:
            problems.append(
                Problem("SKILL.md", f"name is {len(name)} chars; maximum is {MAX_NAME_LENGTH}")
            )
        if name != payload_dir.name:
            problems.append(
                Problem(
                    "SKILL.md",
                    f"frontmatter name {name!r} does not match directory {payload_dir.name!r}",
                    fatal=False,
                )
            )

    description = front.get("description")
    if not isinstance(description, str) or not description.strip():
        problems.append(Problem("SKILL.md", "missing 'description' in frontmatter"))
    else:
        description = description.strip()
        if "<" in description or ">" in description:
            problems.append(
                Problem("SKILL.md", "description cannot contain angle brackets ('<' or '>')")
            )
        if len(description) > MAX_DESCRIPTION_LENGTH:
            problems.append(
                Problem(
                    "SKILL.md",
                    f"description is {len(description)} chars; maximum is {MAX_DESCRIPTION_LENGTH}",
                )
            )

    return problems


CODEX = Codex(
    key="codex",
    label="Codex CLI",
    home_env="CODEX_HOME",
    home_default=".codex",
    skills_subdir="skills",
    project_subdir=".codex/skills",
    project_aliases=(".agents/skills",),
    project_scope_verified=True,
)
