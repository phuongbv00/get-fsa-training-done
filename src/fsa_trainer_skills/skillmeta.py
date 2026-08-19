"""Minimal SKILL.md frontmatter reader.

Deliberately not a YAML parser. It handles exactly the subset both Claude Code
and Codex accept for a skill: a `---` fenced block of `key: value` pairs at the
very top of the file, with optional one-level nesting (used only by `metadata:`)
and optional folded/literal scalars (`>-`, `|`) for long descriptions.

Keeping it dependency-free is the point: the package installs a skill, and a
skill installer that cannot run without PyYAML present is a worse installer.
"""

from __future__ import annotations

import re
from pathlib import Path

FENCE = "---"
_KEY = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_-]+):\s?(?P<value>.*)$")


class FrontmatterError(ValueError):
    pass


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return `(frontmatter_block, body)`. Raises if the fence is missing."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FENCE:
        raise FrontmatterError("file does not start with a '---' frontmatter fence")
    for i in range(1, len(lines)):
        if lines[i].strip() == FENCE:
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    raise FrontmatterError("frontmatter fence is never closed")


def parse_frontmatter(block: str) -> dict[str, object]:
    """Parse the fenced block into a dict. Nested keys become a sub-dict."""
    result: dict[str, object] = {}
    current_parent: str | None = None
    pending_key: str | None = None
    pending_lines: list[str] = []
    pending_style = ""

    def flush() -> None:
        nonlocal pending_key, pending_lines, pending_style
        if pending_key is None:
            return
        joiner = "\n" if pending_style == "|" else " "
        value = joiner.join(line.strip() for line in pending_lines).strip()
        result[pending_key] = value
        pending_key, pending_lines, pending_style = None, [], ""

    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = _KEY.match(raw)
        indent = len(match.group("indent")) if match else None

        if pending_key is not None and (match is None or (indent or 0) > 0):
            pending_lines.append(raw)
            continue
        flush()

        if match is None:
            raise FrontmatterError(f"cannot parse frontmatter line: {raw!r}")

        key, value = match.group("key"), match.group("value").strip()
        if indent:
            if current_parent is None:
                raise FrontmatterError(f"indented key {key!r} has no parent")
            parent = result.setdefault(current_parent, {})
            if not isinstance(parent, dict):
                raise FrontmatterError(f"{current_parent!r} has both a value and children")
            parent[key] = _unquote(value)
            continue

        current_parent = key
        if value in (">", ">-", "|", "|-"):
            pending_key, pending_lines, pending_style = key, [], value[0]
        elif value == "":
            result[key] = {}
        else:
            result[key] = _unquote(value)

    flush()
    return result


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def read_skill_frontmatter(skill_md: Path) -> dict[str, object]:
    block, _ = split_frontmatter(skill_md.read_text(encoding="utf-8"))
    return parse_frontmatter(block)
