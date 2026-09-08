"""Locating a skill's payload by its CLI namespace.

Each skill's payload lives at `skills/<namespace>/payload/<skill-name>/`
inside the package, which resolves identically in an editable checkout, a
wheel, and an sdist without a build hook copying files around.
"""

from __future__ import annotations

from pathlib import Path

from .errors import FsaTrainerSkillsError
from .skills import get as get_skill


def skill_payload(namespace: str) -> Path:
    """Directory of one skill's payload, e.g. `.../assessment/payload/fsa-training-assessment`."""
    skill = get_skill(namespace)
    path = skill.payload_dir
    if not (path / "SKILL.md").is_file():
        raise FsaTrainerSkillsError(
            f"skill payload {skill.name!r} is missing from this installation ({path})",
            hint="reinstall the package; the wheel may have been built without package data",
        )
    return path
