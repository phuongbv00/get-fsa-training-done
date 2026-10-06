"""The skill abstraction: what the registry and lifecycle commands need to
know about a shipped agent skill. Mirrors `platforms/base.py`'s `Platform`.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Skill:
    """One agent skill this package can install and drive.

    `namespace` is the CLI subcommand prefix (`get-fsa-training-done <namespace>
    <verb>`) and the key skills are looked up by (`--skill <namespace>`).
    `name` is the skill's own identity: the SKILL.md `name:` frontmatter, the
    payload directory name, and the default installed directory name.
    """

    name: str  # e.g. "fsa-training-assessment"
    namespace: str  # e.g. "assessment"
    summary: str  # one-line description, used in --help
    payload_dir: Path
    dep_group: str = "core"  # envmgr.stamp.GROUPS key this skill's workers need
    #: Names this skill was installed under before. `install` and `update`
    #: clear a directory left behind under one of these, so a rename does not
    #: leave a second copy advertising the same triggers to the agent.
    previous_names: tuple[str, ...] = ()

    def add_worker_parsers(
        self, subparsers: argparse._SubParsersAction
    ) -> None:  # pragma: no cover - overridden
        raise NotImplementedError

    def doctor_extra(self) -> dict[str, str]:
        """Optional extra environment checks `doctor` should report for this
        skill (e.g. assessment reports the Chrome binary `render` needs)."""
        return {}
