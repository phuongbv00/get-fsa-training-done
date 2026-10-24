"""What a hosted agent gets: the skill as a zip, and the script that installs its CLI.

A hosted agent (Claude Managed Agents) takes the skill as an upload and runs it
in a sandbox that has Python but not this CLI, so `pack` writes the upload and
the payload's `scripts/setup.sh` installs the CLI there.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile

import pytest

from get_fsa_training_done.__about__ import __version__
from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import GftdError
from get_fsa_training_done.lifecycle.install.receipt import RECEIPT_NAME
from get_fsa_training_done.skill import SKILL

SCRIPT = SKILL.payload_dir / "scripts" / "setup.sh"
needs_sh = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("sh") is None, reason="needs a POSIX sh"
)


# --- The upload ---------------------------------------------------------------


def test_pack_writes_one_folder_with_skill_md_at_its_root(isolated_home, tmp_path):
    output = tmp_path / "skill.zip"
    assert main(["pack", str(output)]) == 0
    names = zipfile.ZipFile(output).namelist()
    assert f"{SKILL.name}/SKILL.md" in names
    assert f"{SKILL.name}/scripts/setup.sh" in names
    assert {name.split("/")[0] for name in names} == {SKILL.name}
    assert not any(name.endswith(RECEIPT_NAME) for name in names)


def test_pack_is_reproducible(isolated_home, tmp_path):
    first, second = tmp_path / "a.zip", tmp_path / "b.zip"
    assert main(["pack", str(first)]) == 0
    assert main(["pack", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()


def test_pack_refuses_anything_but_a_zip(isolated_home, tmp_path):
    with pytest.raises(GftdError):
        main(["pack", str(tmp_path / "skill.tar")])


# --- The setup script -----------------------------------------------------------


def fake_cli(path) -> None:
    """A stand-in CLI: reports this version, and builds nothing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'#!/bin/sh\n[ "$1" = --version ] && echo "get-fsa-training-done {__version__}"\nexit 0\n',
        encoding="utf-8",
    )
    path.chmod(0o755)


def run_script(home, path_dirs) -> subprocess.CompletedProcess:
    env = {"HOME": str(home), "PATH": os.pathsep.join([*path_dirs, "/usr/bin", "/bin"])}
    return subprocess.run(["sh", str(SCRIPT)], env=env, capture_output=True, text=True, check=False)


@needs_sh
def test_the_script_uses_a_cli_already_at_its_version(tmp_path):
    bin_dir = tmp_path / "bin"
    fake_cli(bin_dir / "get-fsa-training-done")
    proc = run_script(tmp_path, [str(bin_dir)])
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines()[-1] == "FSA: get-fsa-training-done"
    assert "installing" not in proc.stderr


@needs_sh
def test_the_script_finds_a_cli_it_installed_off_path(tmp_path):
    cli = tmp_path / ".local" / "bin" / "get-fsa-training-done"
    fake_cli(cli)
    proc = run_script(tmp_path, [])
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines()[-1] == f"FSA: {cli}"
