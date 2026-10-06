"""The one agent skill this package ships, and where its payload lives.

Program, material and assessment used to be three skills; they are one now,
installed as `get-fsa-training-done`, because they divide a single job and share
one router, one version and one set of writing rules. The code stays split by
feature under `features/`, and each feature keeps its own CLI namespace.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .__about__ import PACKAGE_NAME
from .errors import FsaTrainerSkillsError


@dataclass(frozen=True)
class Skill:
    """What the lifecycle commands need to know about the shipped skill.

    `name` is the SKILL.md `name:` frontmatter, the payload directory name, and
    the default installed directory name. `dep_group` keys the managed venv the
    feature workers run in.
    """

    name: str
    payload_dir: Path
    dep_group: str = "core"


SKILL = Skill(
    name=PACKAGE_NAME,
    payload_dir=Path(__file__).resolve().parent / "payload" / PACKAGE_NAME,
)


def payload() -> Path:
    """The payload directory, refusing an installation that lost its data files."""
    if not (SKILL.payload_dir / "SKILL.md").is_file():
        raise FsaTrainerSkillsError(
            f"the skill payload is missing from this installation ({SKILL.payload_dir})",
            hint="reinstall the package; the wheel may have been built without package data",
        )
    return SKILL.payload_dir
