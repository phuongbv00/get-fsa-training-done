"""Shared fixtures.

Every test that could touch a real skill directory or the real environment
cache runs against a temporary HOME instead. That is not politeness — the
install tests write and delete skill folders, and pointing them at the
developer's `~/.claude` would delete their actual skill.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Redirect every host and cache location into a temporary directory."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude"))
    monkeypatch.setenv("CODEX_HOME", str(home / ".codex"))
    monkeypatch.setenv("COPILOT_HOME", str(home / ".copilot"))
    monkeypatch.setenv("GET_FSA_TRAINING_DONE_HOME", str(home / "cache"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home / "xdg-cache"))
    monkeypatch.delenv("GET_FSA_TRAINING_DONE_NO_VENV", raising=False)
    # `gftd update` would otherwise ask PyPI for a newer release.
    monkeypatch.setenv("GET_FSA_TRAINING_DONE_NO_SELF_UPDATE", "1")
    return home
