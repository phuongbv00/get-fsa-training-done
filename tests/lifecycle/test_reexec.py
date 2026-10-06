"""Entering the managed venv.

A venv's `bin/python` is normally a symlink to the interpreter that created
it, so "is this the venv's interpreter?" cannot be answered by resolving
paths: the answer is always yes, and the worker then runs without the venv's
libraries. These pin the comparison to the environment instead.
"""

from __future__ import annotations

import sys

import pytest

from get_fsa_training_done.lifecycle.envmgr import bootstrap, reexec, stamp


@pytest.fixture
def venv(tmp_path, monkeypatch):
    """A venv whose python is a symlink to the running interpreter."""
    root = tmp_path / "venv"
    python = stamp.venv_python(root)
    python.parent.mkdir(parents=True)
    python.symlink_to(sys.executable)
    monkeypatch.delenv(reexec.NO_VENV_ENV, raising=False)
    monkeypatch.delenv(reexec.IN_VENV_ENV, raising=False)
    monkeypatch.setattr(bootstrap, "ensure", lambda *groups, offline=False: root)
    return root


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX exec path")
def test_a_venv_symlinked_to_this_interpreter_is_still_entered(venv, monkeypatch):
    calls = []
    monkeypatch.setattr(reexec.os, "execve", lambda *args: calls.append(args))
    reexec.enter("core", argv=["assessment", "render", "x.md"])
    assert calls, "the venv was skipped because its python resolves to ours"
    path, cmd, env = calls[0]
    assert cmd[1:4] == ["-m", "get_fsa_training_done", "assessment"]
    assert env[reexec.IN_VENV_ENV] == "1"


def test_running_inside_the_venv_does_not_re_enter_it(venv, monkeypatch):
    monkeypatch.setattr(reexec.sys, "prefix", str(venv))
    monkeypatch.setattr(reexec.os, "execve", lambda *args: pytest.fail("re-entered"))
    reexec.enter("core", argv=["assessment", "render", "x.md"])
