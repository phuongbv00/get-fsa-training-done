"""`install --cloud`: the setup steps that let a cloud agent use a project's skill.

A cloud agent's container holds a clone of the repository and nothing else, so
the project install has to carry the skill and each host's setup step has to
run the payload's `scripts/setup.sh`, which installs the CLI. `uninstall`
takes back what was added and nothing a user wrote.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pytest

from get_fsa_training_done.__about__ import __version__
from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.lifecycle.commands import cloud
from get_fsa_training_done.lifecycle.platforms.base import universal_root
from get_fsa_training_done.skill import SKILL

SCRIPT = SKILL.payload_dir / "scripts" / "setup.sh"
needs_sh = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("sh") is None, reason="needs a POSIX sh"
)


def install_cloud(project, *args: str) -> int:
    return main(["install", "--cloud", "--project-root", str(project), "--no-prewarm", *args])


def settings(project) -> dict:
    return json.loads((project / cloud.SETTINGS).read_text(encoding="utf-8"))


def test_the_setup_steps_name_a_script_the_payload_ships():
    assert SCRIPT.is_file()
    assert cloud.setup_script(SKILL.name).endswith("/scripts/setup.sh")
    assert cloud.setup_script(SKILL.name) in cloud.claude_hook_command(SKILL.name)
    assert cloud.setup_script(SKILL.name) in cloud.copilot_workflow(SKILL.name)


def test_cloud_installs_into_the_project_for_every_agent(isolated_home, tmp_path):
    project = tmp_path / "proj"
    assert install_cloud(project) == 0

    shared = universal_root("project", project) / SKILL.name
    assert (shared / "scripts" / "setup.sh").is_file()
    assert (project / ".claude" / "skills" / SKILL.name / "SKILL.md").is_file()
    hooks = settings(project)["hooks"]["SessionStart"]
    assert hooks == [
        {"hooks": [{"type": "command", "command": cloud.claude_hook_command(SKILL.name)}]}
    ]
    workflow = (project / cloud.COPILOT_WORKFLOW).read_text(encoding="utf-8")
    assert workflow == cloud.copilot_workflow(SKILL.name)


def test_cloud_refuses_user_scope(isolated_home):
    with pytest.raises(UsageError):
        main(["install", "--cloud", "--scope", "user", "--no-prewarm"])


def test_cloud_keeps_the_users_settings_and_is_idempotent(isolated_home, tmp_path, capsys):
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    mine = {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "echo hi"}]}]}}
    (project / cloud.SETTINGS).write_text(json.dumps(mine), encoding="utf-8")

    assert install_cloud(project) == 0
    assert install_cloud(project) == 0
    entries = settings(project)["hooks"]["SessionStart"]
    assert len(entries) == 2 and entries[0] == mine["hooks"]["SessionStart"][0]
    assert "already runs" in capsys.readouterr().out

    assert main(["uninstall", "--yes", "--project-root", str(project)]) == 0
    assert settings(project) == mine


def test_cloud_leaves_a_users_copilot_workflow_alone(isolated_home, tmp_path, capsys):
    project = tmp_path / "proj"
    workflow = project / cloud.COPILOT_WORKFLOW
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: Copilot Setup Steps\n", encoding="utf-8")

    assert install_cloud(project) == 0
    assert workflow.read_text(encoding="utf-8") == "name: Copilot Setup Steps\n"
    assert "left alone" in capsys.readouterr().out
    assert main(["uninstall", "--yes", "--project-root", str(project)]) == 0
    assert workflow.is_file()


def test_uninstall_takes_back_what_cloud_added(isolated_home, tmp_path):
    project = tmp_path / "proj"
    assert install_cloud(project) == 0
    assert main(["uninstall", "--yes", "--project-root", str(project)]) == 0
    assert not (project / cloud.SETTINGS).exists()
    assert not (project / cloud.COPILOT_WORKFLOW).exists()


def test_cloud_dry_run_writes_nothing(isolated_home, tmp_path):
    project = tmp_path / "proj"
    assert install_cloud(project, "--dry-run") == 0
    assert not project.exists() or not any(project.rglob("*"))


# --- The script itself --------------------------------------------------------


def fake_cli(path) -> None:
    """A stand-in CLI: reports this version, and builds nothing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'#!/bin/sh\n[ "$1" = --version ] && echo "get-fsa-training-done {__version__}"\nexit 0\n',
        encoding="utf-8",
    )
    path.chmod(0o755)


def run_script(home, path_dirs, **env) -> subprocess.CompletedProcess:
    base = {"HOME": str(home), "PATH": os.pathsep.join([*path_dirs, "/usr/bin", "/bin"])}
    return subprocess.run(
        ["sh", str(SCRIPT)], env={**base, **env}, capture_output=True, text=True, check=False
    )


@needs_sh
def test_the_script_uses_a_cli_already_at_its_version(tmp_path):
    bin_dir = tmp_path / "bin"
    fake_cli(bin_dir / "get-fsa-training-done")
    proc = run_script(tmp_path, [str(bin_dir)])
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines()[-1] == "FSA: get-fsa-training-done"
    assert "installing" not in proc.stderr


@needs_sh
def test_the_script_puts_a_cli_off_path_on_the_sessions_path(tmp_path):
    cli = tmp_path / ".local" / "bin" / "get-fsa-training-done"
    fake_cli(cli)
    env_file = tmp_path / "claude.env"
    env_file.write_text("", encoding="utf-8")

    proc = run_script(tmp_path, [], CLAUDE_ENV_FILE=str(env_file))
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines()[-1] == f"FSA: {cli}"
    assert env_file.read_text(encoding="utf-8") == f'export PATH="{cli.parent}:$PATH"\n'


# --- Hosted agents: the skill as an upload --------------------------------------


def test_pack_writes_one_folder_with_skill_md_at_its_root(isolated_home, tmp_path):
    import zipfile

    from get_fsa_training_done.lifecycle.install.receipt import RECEIPT_NAME

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
    from get_fsa_training_done.errors import GftdError

    with pytest.raises(GftdError):
        main(["pack", str(tmp_path / "skill.tar")])
