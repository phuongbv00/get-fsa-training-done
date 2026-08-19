"""Platform lookup. Adding a host means adding a module and one entry here."""

from __future__ import annotations

from ..errors import UsageError
from .base import SCOPES, Platform, Problem
from .claude import CLAUDE
from .codex import CODEX

_PLATFORMS: dict[str, Platform] = {p.key: p for p in (CLAUDE, CODEX)}

ALL = "all"


def names() -> list[str]:
    return list(_PLATFORMS)


def get(key: str) -> Platform:
    try:
        return _PLATFORMS[key]
    except KeyError:
        raise UsageError(
            f"unknown platform {key!r}; choose from {', '.join(names())} or '{ALL}'"
        ) from None


def resolve(key: str) -> list[Platform]:
    """`'all'` expands to every platform; anything else is a single lookup."""
    if key == ALL:
        return list(_PLATFORMS.values())
    return [get(key)]


def check_scope(scope: str) -> str:
    if scope not in SCOPES:
        raise UsageError(f"unknown scope {scope!r}; choose from {', '.join(SCOPES)}")
    return scope


__all__ = ["ALL", "Platform", "Problem", "check_scope", "get", "names", "resolve"]
