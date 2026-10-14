"""Install, update, and uninstall — including the cases that risk losing work.

Every test takes the `skill` fixture, the one skill the package ships. The
skill lives once in `.agents/skills`; agents that do not read that folder get
a symlink into it. Where the OS refuses symlinks (Windows without Developer
Mode) each of them gets a copy instead, so the assertions that only hold for a
link are guarded by `links.supported()`.
"""

from __future__ import annotations

import json
import os
import re

import pytest

from get_fsa_training_done.__about__ import __version__
from get_fsa_training_done.cli import main
from get_fsa_training_done.errors import NotInstalledError
from get_fsa_training_done.lifecycle.install import links
from get_fsa_training_done.lifecycle.install import receipt as receipt_mod
from get_fsa_training_done.lifecycle.platforms import registry
from get_fsa_training_done.lifecycle.platforms.base import universal_root
from get_fsa_training_done.skill import SKILL

LINKS = links.supported()
needs_links = pytest.mark.skipif(not LINKS, reason="this system cannot make symlinks")


@pytest.fixture
def skill():
    return SKILL


def dest_for(skill, platform: str, scope: str = "user", project_root=None):
    return registry.get(platform).dest(scope, skill.name, project_root)


def shared_for(skill, scope: str = "user", project_root=None):
    return universal_root(scope, project_root) / skill.name


def gone(path) -> bool:
    """Neither a folder nor a (possibly dangling) symlink is left at `path`."""
    return not path.exists() and not path.is_symlink()


def install(*args: str) -> int:
    return main(["install", *args, "--no-prewarm"])


def old_copy(path, key: str) -> None:
    """A plain copy at `path` for one agent, as releases before the shared copy wrote."""
    from argparse import Namespace

    from get_fsa_training_done.lifecycle.commands.deploy import install_copy

    args = Namespace(dry_run=False, verbose=False, force=False)
    install_copy(SKILL, SKILL.name, key, "user", path, args, SKILL.payload_dir, [key])


# --- Where the skill goes ---------------------------------------------------


def test_install_writes_one_copy_and_links_claude_to_it(isolated_home, skill):
    assert install("--platform", "claude") == 0
    shared, dest = shared_for(skill), dest_for(skill, "claude")

    if LINKS:
        assert links.points_to(dest, shared)
        assert not os.path.isabs(os.readlink(dest)), "a relative link survives a move"
        receipt = receipt_mod.read(shared)
        assert receipt.agents == ["claude"]
        assert receipt.links == [str(dest)]
    else:
        assert not shared.exists()
    receipt = receipt_mod.read(dest)
    assert receipt.version == __version__ and receipt.skill_name == skill.name
    assert (dest / "SKILL.md").is_file()
    # The receipt must record how to call back into the CLI: `npx` leaves
    # nothing on PATH, so the skill would otherwise have no way to find it.
    assert receipt.cli["invocation"][-2:] == ["-m", "get_fsa_training_done"]


def test_codex_and_copilot_read_the_shared_copy_itself(isolated_home, skill):
    assert install("--platform", "all") == 0
    shared = shared_for(skill)
    assert dest_for(skill, "codex") == shared == dest_for(skill, "copilot")
    assert shared.is_dir() and not shared.is_symlink()
    assert set(receipt_mod.read(shared).agents) == {"claude", "codex", "copilot", "antigravity"}
    for key in ("claude", "antigravity"):
        dest = dest_for(skill, key)
        assert links.points_to(dest, shared) if LINKS else (dest / "SKILL.md").is_file()


def test_antigravity_reads_the_shared_copy_in_a_project(isolated_home, tmp_path, skill):
    project = tmp_path / "proj"
    assert (
        install("--platform", "antigravity", "--scope", "project", "--project-root", str(project))
        == 0
    )
    assert dest_for(skill, "antigravity", "project", project) == shared_for(
        skill, "project", project
    )
    assert (project / ".agents" / "skills" / skill.name / "SKILL.md").is_file()


def test_install_is_idempotent(isolated_home, skill, capsys):
    install("--platform", "claude")
    capsys.readouterr()
    assert install("--platform", "claude") == 0
    assert "already installed" in capsys.readouterr().out


def test_install_refuses_an_unmanaged_destination(isolated_home, skill, capsys):
    dest = dest_for(skill, "claude")
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("someone else's skill", encoding="utf-8")

    assert install("--platform", "claude") == 1
    assert "not installed by get-fsa-training-done" in capsys.readouterr().out
    assert (dest / "SKILL.md").read_text(encoding="utf-8") == "someone else's skill"
    assert gone(shared_for(skill)), "no shared copy that nobody would read"


def test_force_adopts_an_unmanaged_destination(isolated_home, skill):
    dest = dest_for(skill, "claude")
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("someone else's skill", encoding="utf-8")

    assert install("--platform", "claude", "--force") == 0
    assert skill.name in (dest / "SKILL.md").read_text(encoding="utf-8")
    assert (dest / "SKILL.md.bak").is_file()


def test_dry_run_writes_nothing(isolated_home, skill):
    assert main(["install", "--platform", "all", "--dry-run"]) == 0
    assert gone(dest_for(skill, "claude"))
    assert gone(shared_for(skill))


def test_without_symlinks_every_agent_gets_a_copy(isolated_home, skill, monkeypatch):
    monkeypatch.setattr(links, "_SUPPORTED", False)
    assert install("--platform", "claude") == 0
    dest = dest_for(skill, "claude")
    assert not dest.is_symlink() and (dest / "SKILL.md").is_file()
    assert gone(shared_for(skill))
    assert main(["uninstall", "--yes"]) == 0
    assert gone(dest)


# --- Update -----------------------------------------------------------------


def test_update_never_overwrites_a_user_edit(isolated_home, skill):
    install("--platform", "claude")
    dest = dest_for(skill, "claude")
    edited = dest / "SKILL.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nmy note\n", encoding="utf-8")

    assert main(["update"]) == 0
    assert "my note" in edited.read_text(encoding="utf-8")
    assert (dest / "SKILL.md.new").is_file()


def test_a_conflicted_file_is_not_claimed_by_the_receipt(isolated_home, skill):
    """Otherwise uninstall would delete content the user wrote."""
    install("--platform", "claude")
    dest = dest_for(skill, "claude")
    edited = dest / "SKILL.md"
    edited.write_text("mine\n", encoding="utf-8")
    main(["update"])

    receipt = receipt_mod.read(dest)
    assert "SKILL.md" not in {record.path for record in receipt.files}

    main(["uninstall", "--yes"])
    # The link stays while the user's file does, so it is still where it was.
    assert edited.read_text(encoding="utf-8") == "mine\n"


def test_update_check_reports_up_to_date(isolated_home, skill):
    install("--platform", "claude")
    assert main(["update", "--check"]) == 0


def test_update_check_flags_an_older_install(isolated_home, skill):
    install("--platform", "claude")
    shared = receipt_mod.read(dest_for(skill, "claude")).dest
    receipt = receipt_mod.read(dest_for(skill, "claude"))
    receipt.version = "0.0.1"
    receipt_mod.write(type(shared_for(skill))(shared), receipt)
    assert main(["update", "--check"]) == 1


def test_update_for_an_agent_that_has_nothing(isolated_home, skill):
    install("--platform", "claude")
    with pytest.raises(NotInstalledError):
        main(["update", "--platform", "antigravity"])


def test_bare_update_upgrades_every_install(isolated_home, tmp_path, skill, monkeypatch, capsys):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    install("--platform", "claude")
    install("--platform", "copilot")
    install("--platform", "codex", "--scope", "project")
    copies = [shared_for(skill), shared_for(skill, "project")]
    for copy in copies:
        receipt = receipt_mod.read(copy)
        receipt.version = "0.0.1"
        receipt_mod.write(copy, receipt)
    capsys.readouterr()

    assert main(["update"]) == 0
    assert "found 2 install(s)" in capsys.readouterr().out
    assert [receipt_mod.read(c).version for c in copies] == [__version__] * 2
    # Antigravity was never installed, so update did not link it in.
    assert gone(dest_for(skill, "antigravity"))
    assert set(receipt_mod.read(copies[0]).agents) == {"claude", "copilot"}


def test_bare_update_with_nothing_installed(isolated_home, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(NotInstalledError):
        main(["update"])


# --- Moving what earlier releases installed ---------------------------------


@pytest.mark.parametrize(
    ("key", "legacy"),
    [("codex", ".codex/skills"), ("copilot", ".copilot/skills")],
)
def test_update_moves_an_earlier_user_install(isolated_home, skill, capsys, key, legacy):
    old = isolated_home / legacy / skill.name
    old_copy(old, key)
    capsys.readouterr()

    assert main(["update", "--check"]) == 1
    assert "earlier release" in capsys.readouterr().out
    assert main(["update"]) == 0
    assert gone(old)
    assert receipt_mod.read(shared_for(skill)).agents == [key]


def test_update_moves_an_earlier_project_install(isolated_home, tmp_path, skill, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    old = project / ".github" / "skills" / skill.name
    old_copy(old, "copilot")
    assert main(["update"]) == 0
    assert gone(old)
    assert (project / ".agents" / "skills" / skill.name / "SKILL.md").is_file()


def test_moving_keeps_what_the_user_edited(isolated_home, skill):
    old = isolated_home / ".codex" / "skills" / skill.name
    old_copy(old, "codex")
    (old / "NOTES.md").write_text("mine", encoding="utf-8")
    assert main(["update"]) == 0
    assert (old / "NOTES.md").read_text(encoding="utf-8") == "mine"
    assert not (old / "SKILL.md").exists()


@needs_links
def test_update_turns_an_earlier_copy_into_a_link(isolated_home, skill):
    dest = dest_for(skill, "claude")
    old_copy(dest, "claude")
    assert not dest.is_symlink()
    assert main(["update"]) == 0
    assert links.points_to(dest, shared_for(skill))


@needs_links
def test_an_edited_earlier_copy_stays_a_copy(isolated_home, skill, capsys):
    dest = dest_for(skill, "claude")
    old_copy(dest, "claude")
    receipt = receipt_mod.read(dest)
    receipt.version = "0.0.1"
    receipt_mod.write(dest, receipt)
    (dest / "NOTES.md").write_text("mine", encoding="utf-8")

    assert main(["update"]) == 0
    assert not dest.is_symlink()
    assert receipt_mod.read(dest).version == __version__
    assert (dest / "NOTES.md").read_text(encoding="utf-8") == "mine"


# --- Uninstall --------------------------------------------------------------


def test_uninstall_removes_everything_it_wrote(isolated_home, skill):
    install("--platform", "all")
    assert main(["uninstall", "--yes"]) == 0
    for key in ("claude", "codex", "copilot", "antigravity"):
        assert gone(dest_for(skill, key))
    assert gone(shared_for(skill))


def test_uninstall_keeps_files_it_did_not_write(isolated_home, skill):
    install("--platform", "claude")
    dest = dest_for(skill, "claude")
    (dest / "NOTES.md").write_text("mine", encoding="utf-8")

    main(["uninstall", "--yes"])
    assert (dest / "NOTES.md").read_text(encoding="utf-8") == "mine"
    assert not (dest / "SKILL.md").exists()


def test_uninstall_without_a_terminal_needs_yes(isolated_home, skill, capsys):
    install("--platform", "claude")
    assert main(["uninstall"]) == 1
    assert "pass --yes" in capsys.readouterr().out
    assert (dest_for(skill, "claude") / "SKILL.md").is_file()


def test_uninstall_no_longer_takes_a_platform(isolated_home):
    with pytest.raises(SystemExit):
        main(["uninstall", "--platform", "claude"])


@pytest.mark.parametrize("command", ["install", "update"])
def test_no_command_takes_a_dir(isolated_home, tmp_path, command):
    with pytest.raises(SystemExit):
        main([command, "--dir", str(tmp_path / "x")])


def test_uninstall_leaves_a_folder_it_did_not_install(isolated_home, skill, capsys):
    dest = dest_for(skill, "claude")
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("not ours", encoding="utf-8")

    assert main(["uninstall", "--yes"]) == 0
    assert "not installed anywhere" in capsys.readouterr().out
    assert (dest / "SKILL.md").is_file()


def test_uninstall_removes_an_earlier_install_too(isolated_home, skill):
    old = isolated_home / ".codex" / "skills" / skill.name
    old_copy(old, "codex")
    install("--platform", "claude")
    assert main(["uninstall", "--yes"]) == 0
    assert gone(old) and gone(shared_for(skill)) and gone(dest_for(skill, "claude"))


@pytest.mark.parametrize("platform", ["claude", "codex", "copilot", "antigravity"])
@pytest.mark.parametrize("scope", ["user", "project"])
def test_every_target_round_trips(isolated_home, tmp_path, skill, platform, scope):
    project = tmp_path / "proj"
    args = ["--platform", platform, "--scope", scope, "--project-root", str(project)]

    assert install(*args) == 0
    dest = dest_for(skill, platform, scope, project if scope == "project" else None)
    assert (dest / "SKILL.md").is_file()
    assert main(["uninstall", "--yes", "--project-root", str(project)]) == 0
    assert gone(dest)
    assert gone(shared_for(skill, scope, project))


# --- Status -----------------------------------------------------------------


@needs_links
def test_status_shows_where_a_link_points(isolated_home, skill, capsys):
    install("--platform", "claude")
    capsys.readouterr()
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert f"{skill.name} → " in out
    assert out.rstrip().endswith(os.path.join(".agents", "skills", skill.name))


def test_status_lists_only_the_agents_installed_for(isolated_home, skill, capsys, monkeypatch):
    """Run from home, a project's `.agents/skills` is the user-scope copy.

    Copilot reads that copy and Antigravity reads it at project scope, but
    neither was installed for; status used to list both.
    """
    monkeypatch.chdir(isolated_home)
    install("--platform", "codex")
    install("--platform", "claude")
    capsys.readouterr()

    assert main(["status", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)["installs"]
    assert sorted((row["platform"], row["scope"]) for row in rows) == [
        ("claude", "user"),
        ("codex", "user"),
    ]


def test_status_prints_a_table(isolated_home, skill, capsys):
    install("--platform", "claude")
    capsys.readouterr()
    assert main(["status"]) == 0
    lines = capsys.readouterr().out.splitlines()
    header = next(line for line in lines if line.strip().startswith("Agent"))
    assert header.split() == ["Agent", "Scope", "Version", "State", "Location"]
    row = next(line for line in lines if "Claude Code" in line)
    assert "global" in row and "up to date" in row
    # Columns line up: the row's version starts where the header's does.
    assert row.index(__version__) == header.index("Version")


def test_status_json_reports_the_install(isolated_home, skill, capsys):
    base = ["--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    capsys.readouterr()
    assert main(["status", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["package_version"] == __version__
    assert any(
        row["platform"] == "claude" and row["current"] and row["skill"] == skill.name
        for row in report["installs"]
    )


def test_status_reports_a_collapsed_scope_once(isolated_home, skill, capsys):
    """User and project scope can name the same directory; that is one install.

    Running `status` from the directory that holds the user-scope config — the
    home directory, normally — makes `<cwd>/.claude/skills` and
    `~/.claude/skills` the same folder. Reporting it under both scopes invented
    a project install that was never there.
    """
    base = ["--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    capsys.readouterr()

    assert main(["status", *base, "--project-root", str(isolated_home), "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)["installs"]

    assert len(rows) == 1, f"one directory, one row; got {[row['scope'] for row in rows]}"
    assert rows[0]["scope"] == "user"


def test_status_still_reports_a_genuinely_separate_project_install(
    isolated_home, skill, tmp_path, capsys
):
    project = tmp_path / "proj"
    base = ["--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    main(["install", *base, "--scope", "project", "--project-root", str(project), "--no-prewarm"])
    capsys.readouterr()

    assert main(["status", *base, "--project-root", str(project), "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)["installs"]

    assert {row["scope"] for row in rows} == {"user", "project"}


# --- Self-update from PyPI --------------------------------------------------


@pytest.fixture
def pypi(monkeypatch):
    """Turn the PyPI check back on, against a fake index and a fake installer."""
    from get_fsa_training_done.lifecycle import selfupdate

    monkeypatch.delenv(selfupdate.DISABLE_ENV)
    calls = {"upgrade": [], "rerun": []}
    state = {"latest": __version__, "kind": "pip"}
    monkeypatch.setattr(selfupdate, "latest_version", lambda: state["latest"])
    monkeypatch.setattr(selfupdate, "install_kind", lambda: state["kind"])
    monkeypatch.setattr(selfupdate, "upgrade", lambda kind, v: calls["upgrade"].append((kind, v)))
    monkeypatch.setattr(selfupdate, "rerun", lambda argv: calls["rerun"].append(argv) or 0)
    return state, calls


def test_update_upgrades_from_pypi_then_reruns(isolated_home, skill, pypi):
    state, calls = pypi
    state["latest"] = "99.0.0"
    install("--platform", "claude")
    assert main(["update", "--platform", "claude"]) == 0
    assert calls["upgrade"] == [("pip", "99.0.0")]
    assert calls["rerun"] == [["update", "--platform", "claude"]]


def test_update_stays_put_when_pypi_is_not_newer(isolated_home, skill, pypi):
    _, calls = pypi
    install("--platform", "claude")
    assert main(["update", "--platform", "claude"]) == 0
    assert calls == {"upgrade": [], "rerun": []}


@pytest.mark.parametrize("flag", ["--no-self-update", "--offline", "--dry-run"])
def test_update_flags_that_never_upgrade(isolated_home, skill, pypi, flag):
    state, calls = pypi
    state["latest"] = "99.0.0"
    install("--platform", "claude")
    assert main(["update", "--platform", "claude", flag]) == 0
    assert calls == {"upgrade": [], "rerun": []}


def test_update_check_flags_a_newer_pypi_release(isolated_home, skill, pypi, capsys):
    state, calls = pypi
    state["latest"] = "99.0.0"
    install("--platform", "claude")
    assert main(["update", "--platform", "claude", "--check"]) == 1
    assert "99.0.0 on PyPI" in capsys.readouterr().out
    assert calls["upgrade"] == []


def test_update_leaves_an_editable_checkout_alone(isolated_home, skill, pypi, capsys):
    state, calls = pypi
    state["latest"], state["kind"] = "99.0.0", "editable"
    install("--platform", "claude")
    assert main(["update", "--platform", "claude"]) == 0
    assert "pull it to upgrade" in capsys.readouterr().out
    assert calls["upgrade"] == []


def test_version_ordering():
    from get_fsa_training_done.lifecycle.selfupdate import is_newer

    assert is_newer("1.0.10", "1.0.9")
    assert not is_newer("1.0.1", "1.0.1")
    assert not is_newer("0.9.0", "1.0.0")


# --- Interactive install and uninstall --------------------------------------


@pytest.fixture
def terminal(monkeypatch, tmp_path):
    """Pretend a person is at a terminal, pressing the keys a test scripts."""
    from get_fsa_training_done.lifecycle import prompt

    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setattr(prompt, "is_interactive", lambda: True)
    pressed: list[str] = []

    def script(*sequence: str) -> None:
        pressed[:] = sequence

    def read_key() -> str:
        if not pressed:
            raise AssertionError("the prompt asked for a key the test did not script")
        return pressed.pop(0)

    monkeypatch.setattr(prompt, "read_key", read_key)
    return script


def test_bare_install_asks_then_shows_the_summary(isolated_home, skill, terminal, capsys):
    # Tick Claude Code and Codex, take Global, say yes.
    terminal("space", "down", "space", "enter", "enter", "y")
    assert install() == 0
    assert set(receipt_mod.read(shared_for(skill)).agents) == {"claude", "codex"}
    assert gone(dest_for(skill, "antigravity"))
    out = capsys.readouterr().out
    assert "Which agents do you want to install to?" in out
    assert "Installation Summary" in out
    assert "universal: Codex" in out
    assert "also read by: GitHub Copilot" in out
    assert "Proceed with installation?" in out
    if LINKS:
        assert "symlink → Claude Code" in out


def test_bare_install_in_project_scope(isolated_home, skill, terminal, tmp_path):
    terminal("space", "enter", "down", "enter", "enter")
    assert install() == 0
    project = tmp_path / "proj"
    assert (dest_for(skill, "claude", "project", project) / "SKILL.md").is_file()
    assert gone(dest_for(skill, "claude"))


@pytest.mark.parametrize(
    "keys", [("space", "enter", "enter", "n"), ("space", "enter", "enter", "right", "enter")]
)
def test_declining_the_install_writes_nothing(isolated_home, skill, terminal, capsys, keys):
    terminal(*keys)
    assert install() == 1
    assert gone(dest_for(skill, "claude")) and gone(shared_for(skill))
    assert "nothing was written" in capsys.readouterr().out


def test_the_picker_starts_with_nothing_ticked(isolated_home, skill, terminal, capsys):
    # Even with an agent's config folder present, enter alone is refused.
    registry.get("claude").home().mkdir(parents=True)
    terminal("enter", "esc")
    assert install() == 1
    assert "Select at least one agent" in capsys.readouterr().out
    assert gone(dest_for(skill, "claude"))


@pytest.mark.parametrize("flags", [["--yes"], ["--platform", "claude"], ["--scope", "user"]])
def test_flags_skip_the_picker(isolated_home, skill, terminal, flags):
    terminal()  # any key read fails the test
    assert install(*flags) == 0
    assert receipt_mod.read(dest_for(skill, "claude")) is not None


def _install_user_and_project(skill):
    install("--platform", "claude")
    install("--platform", "codex", "--scope", "project")
    return [dest_for(skill, "claude"), dest_for(skill, "codex", "project")]


def test_bare_uninstall_shows_everything_then_removes_it_all(
    isolated_home, skill, terminal, capsys
):
    dests = _install_user_and_project(skill)
    capsys.readouterr()
    terminal("y")
    assert main(["uninstall"]) == 0
    assert all(gone(d) for d in dests)
    assert gone(shared_for(skill))
    out = capsys.readouterr().out
    assert "Uninstall Summary" in out
    assert "./.agents/skills/get-fsa-training-done" in out
    assert re.search(r"removes: \d+ files", out)
    assert "Proceed with uninstall?" in out


@pytest.mark.parametrize("keys", [("n",), ("enter",), ("esc",)])
def test_bare_uninstall_removes_nothing_unless_told_yes(isolated_home, skill, terminal, keys):
    dests = _install_user_and_project(skill)
    terminal(*keys)
    assert main(["uninstall"]) == 1
    assert all((d / "SKILL.md").is_file() for d in dests)


def test_bare_uninstall_names_and_keeps_an_edited_file(isolated_home, skill, terminal, capsys):
    dests = _install_user_and_project(skill)
    (dests[0] / "NOTES.md").write_text("mine", encoding="utf-8")
    capsys.readouterr()
    terminal("y")
    assert main(["uninstall"]) == 0
    assert "keeps: NOTES.md (edited or added by you)" in capsys.readouterr().out
    assert (dests[0] / "NOTES.md").read_text(encoding="utf-8") == "mine"
    assert gone(dests[1])


def test_bare_uninstall_dry_run_only_previews(isolated_home, skill, terminal, capsys):
    dests = _install_user_and_project(skill)
    capsys.readouterr()
    terminal()
    assert main(["uninstall", "--dry-run"]) == 0
    assert "Uninstall Summary (dry run)" in capsys.readouterr().out
    assert all((d / "SKILL.md").is_file() for d in dests)


def test_bare_uninstall_with_nothing_installed(isolated_home, skill, terminal, capsys):
    terminal()
    assert main(["uninstall"]) == 0
    assert "not installed anywhere" in capsys.readouterr().out
