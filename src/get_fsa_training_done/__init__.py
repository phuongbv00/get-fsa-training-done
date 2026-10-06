"""get-fsa-training-done — a CLI that installs and drives FSA training-tool
agent skills into Claude Code and Codex.

The package ships one CLI over a registry of skills (see `skills/`). Each
skill contributes its own agent-skill payload (a `SKILL.md` a model follows)
and its own worker commands, reached under `get-fsa-training-done <namespace>
<verb>`. Lifecycle commands (`install`, `update`, `uninstall`, `status`,
`doctor`, `env`) are shared and operate across every registered skill.
"""

from .__about__ import CLI_NAME, PACKAGE_NAME, __version__

__all__ = ["CLI_NAME", "PACKAGE_NAME", "__version__"]
