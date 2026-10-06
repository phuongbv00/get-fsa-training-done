"""get-fsa-training-done — one agent skill for FSA training, and the CLI that
installs it into Claude Code and Codex and does its deterministic work.

The skill's payload (`payload/`, a `SKILL.md` a model follows and the
references it routes to) is installed by the lifecycle commands in
`lifecycle/` (`install`, `update`, `uninstall`, `status`, `doctor`, `env`).
Its three features — program, material, assessment — live in `features/`, each
with worker commands under `gftd <namespace> <verb>`.
"""

from .__about__ import CLI_NAME, PACKAGE_NAME, __version__

__all__ = ["CLI_NAME", "PACKAGE_NAME", "__version__"]
