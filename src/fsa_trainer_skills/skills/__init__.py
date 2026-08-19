"""Skill registry. A skill is a subpackage here exporting `SKILL: Skill`.

Adding a skill means adding a subpackage — nothing here, in `cli.py`, or in
any lifecycle command changes.
"""

from __future__ import annotations

import importlib
import pkgutil

from ..errors import UsageError
from ..skillkit import Skill

ALL = "all"


def _discover() -> dict[str, Skill]:
    found: dict[str, Skill] = {}
    for info in pkgutil.iter_modules(__path__):
        if not info.ispkg or info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        skill = getattr(module, "SKILL", None)
        if not isinstance(skill, Skill):
            continue
        if skill.namespace in found:
            raise ValueError(f"duplicate skill namespace {skill.namespace!r}")
        found[skill.namespace] = skill
    return found


_SKILLS = _discover()


def all_skills() -> list[Skill]:
    return list(_SKILLS.values())


def names() -> list[str]:
    return list(_SKILLS)


def get(namespace: str) -> Skill:
    try:
        return _SKILLS[namespace]
    except KeyError:
        raise UsageError(
            f"unknown skill {namespace!r}; choose from {', '.join(_SKILLS)} or {ALL!r}"
        ) from None


def resolve(namespace: str) -> list[Skill]:
    """`'all'` expands to every skill; anything else is a single lookup."""
    return list(_SKILLS.values()) if namespace == ALL else [get(namespace)]


__all__ = ["ALL", "all_skills", "get", "names", "resolve"]
