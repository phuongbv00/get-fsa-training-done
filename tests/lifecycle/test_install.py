"""Install, update, and uninstall — including the cases that risk losing work.

Every test takes the `skill` fixture, the one skill the package ships.
"""

from __future__ import annotations

import json

import pytest

from get_fsa_training_done.__about__ import __version__
from get_fsa_training_done.cli import main
from get_fsa_training_done.lifecycle.install import receipt as receipt_mod
from get_fsa_training_done.lifecycle.platforms import registry
from get_fsa_training_done.skill import SKILL


@pytest.fixture
def skill():
    return SKILL


def dest_for(skill, platform: str, home=None) -> object:
    return registry.get(platform).dest("user", skill.name)


def test_install_creates_receipt_and_files(isolated_home, skill):
    args = ["--platform", "claude", "--no-prewarm"]
    assert main(["install", *args]) == 0
    dest = dest_for(skill, "claude")
    assert (dest / "SKILL.md").is_file()

    receipt = receipt_mod.read(dest)
    assert receipt is not None
    assert receipt.version == __version__
    assert receipt.skill_name == skill.name
    # The receipt must record how to call back into the CLI: `npx` leaves
    # nothing on PATH, so the skill would otherwise have no way to find it.
    assert receipt.cli["invocation"][-2:] == ["-m", "get_fsa_training_done"]
    assert receipt.files


def test_install_is_idempotent(isolated_home, skill, capsys):
    args = ["--platform", "claude", "--no-prewarm"]
    main(["install", *args])
    capsys.readouterr()
    assert main(["install", *args]) == 0
    assert "already installed" in capsys.readouterr().out


def test_install_refuses_an_unmanaged_destination(isolated_home, skill, capsys):
    dest = dest_for(skill, "claude")
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("someone else's skill", encoding="utf-8")

    args = ["--platform", "claude", "--no-prewarm"]
    assert main(["install", *args]) == 1
    assert "not installed by get-fsa-training-done" in capsys.readouterr().out
    assert (dest / "SKILL.md").read_text(encoding="utf-8") == "someone else's skill"


def test_force_adopts_an_unmanaged_destination(isolated_home, skill):
    dest = dest_for(skill, "claude")
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("someone else's skill", encoding="utf-8")

    args = ["--platform", "claude", "--force", "--no-prewarm"]
    assert main(["install", *args]) == 0
    assert skill.name in (dest / "SKILL.md").read_text(encoding="utf-8")
    assert (dest / "SKILL.md.bak").is_file()


def test_dry_run_writes_nothing(isolated_home, skill):
    args = ["--platform", "claude", "--dry-run"]
    assert main(["install", *args]) == 0
    assert not dest_for(skill, "claude").exists()


def test_update_never_overwrites_a_user_edit(isolated_home, skill):
    base = ["--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    dest = dest_for(skill, "claude")
    edited = dest / "SKILL.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nmy note\n", encoding="utf-8")

    assert main(["update", *base]) == 0
    assert "my note" in edited.read_text(encoding="utf-8")
    assert (dest / "SKILL.md.new").is_file()


def test_a_conflicted_file_is_not_claimed_by_the_receipt(isolated_home, skill):
    """Otherwise uninstall would delete content the user wrote."""
    base = ["--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    dest = dest_for(skill, "claude")
    edited = dest / "SKILL.md"
    edited.write_text("mine\n", encoding="utf-8")
    main(["update", *base])

    receipt = receipt_mod.read(dest)
    assert "SKILL.md" not in {record.path for record in receipt.files}

    main(["uninstall", *base])
    assert edited.read_text(encoding="utf-8") == "mine\n"


def test_uninstall_removes_everything_it_wrote(isolated_home, skill):
    base = ["--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    dest = dest_for(skill, "claude")
    assert main(["uninstall", *base]) == 0
    assert not dest.exists()


def test_uninstall_keeps_files_it_did_not_write(isolated_home, skill):
    base = ["--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    dest = dest_for(skill, "claude")
    (dest / "NOTES.md").write_text("mine", encoding="utf-8")

    main(["uninstall", *base])
    assert (dest / "NOTES.md").read_text(encoding="utf-8") == "mine"
    assert not (dest / "SKILL.md").exists()


def test_uninstall_refuses_an_unmanaged_directory(isolated_home, skill, capsys):
    dest = dest_for(skill, "claude")
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("not ours", encoding="utf-8")

    args = ["--platform", "claude"]
    assert main(["uninstall", *args]) == 1
    assert "no get-fsa-training-done receipt" in capsys.readouterr().out
    assert (dest / "SKILL.md").is_file()


def test_update_check_reports_up_to_date(isolated_home, skill):
    base = ["--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    assert main(["update", *base, "--check"]) == 0


def test_update_check_flags_an_older_install(isolated_home, skill):
    base = ["--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    dest = dest_for(skill, "claude")
    receipt = receipt_mod.read(dest)
    receipt.version = "0.0.1"
    receipt_mod.write(dest, receipt)
    assert main(["update", *base, "--check"]) == 1


@pytest.mark.parametrize("platform", ["claude", "codex", "copilot"])
@pytest.mark.parametrize("scope", ["user", "project"])
def test_every_target_round_trips(isolated_home, tmp_path, skill, platform, scope):
    args = ["--platform", platform, "--scope", scope]
    if scope == "project":
        args += ["--project-root", str(tmp_path / "proj")]

    assert main(["install", *args, "--no-prewarm"]) == 0
    dest = registry.get(platform).dest(
        scope, skill.name, (tmp_path / "proj") if scope == "project" else None
    )
    assert (dest / "SKILL.md").is_file()
    assert main(["uninstall", *args]) == 0
    assert not dest.exists()


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
    main(["install", "--platform", "claude", "--no-prewarm"])
    assert main(["update", "--platform", "claude"]) == 0
    assert calls["upgrade"] == [("pip", "99.0.0")]
    assert calls["rerun"] == [["update", "--platform", "claude"]]


def test_update_stays_put_when_pypi_is_not_newer(isolated_home, skill, pypi):
    _, calls = pypi
    main(["install", "--platform", "claude", "--no-prewarm"])
    assert main(["update", "--platform", "claude"]) == 0
    assert calls == {"upgrade": [], "rerun": []}


@pytest.mark.parametrize("flag", ["--no-self-update", "--offline", "--dry-run"])
def test_update_flags_that_never_upgrade(isolated_home, skill, pypi, flag):
    state, calls = pypi
    state["latest"] = "99.0.0"
    main(["install", "--platform", "claude", "--no-prewarm"])
    assert main(["update", "--platform", "claude", flag]) == 0
    assert calls == {"upgrade": [], "rerun": []}


def test_update_check_flags_a_newer_pypi_release(isolated_home, skill, pypi, capsys):
    state, calls = pypi
    state["latest"] = "99.0.0"
    main(["install", "--platform", "claude", "--no-prewarm"])
    assert main(["update", "--platform", "claude", "--check"]) == 1
    assert "99.0.0 on PyPI" in capsys.readouterr().out
    assert calls["upgrade"] == []


def test_update_leaves_an_editable_checkout_alone(isolated_home, skill, pypi, capsys):
    state, calls = pypi
    state["latest"], state["kind"] = "99.0.0", "editable"
    main(["install", "--platform", "claude", "--no-prewarm"])
    assert main(["update", "--platform", "claude"]) == 0
    assert "pull it to upgrade" in capsys.readouterr().out
    assert calls["upgrade"] == []


def test_version_ordering():
    from get_fsa_training_done.lifecycle.selfupdate import is_newer

    assert is_newer("1.0.10", "1.0.9")
    assert not is_newer("1.0.1", "1.0.1")
    assert not is_newer("0.9.0", "1.0.0")


def test_bare_update_upgrades_every_install(isolated_home, tmp_path, skill, monkeypatch, capsys):
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.chdir(project)
    main(["install", "--platform", "claude", "--no-prewarm"])
    main(["install", "--platform", "copilot", "--no-prewarm"])
    main(["install", "--platform", "codex", "--scope", "project", "--no-prewarm"])
    dests = [
        registry.get("claude").dest("user", skill.name),
        registry.get("copilot").dest("user", skill.name),
        registry.get("codex").dest("project", skill.name),
    ]
    for dest in dests:
        receipt = receipt_mod.read(dest)
        receipt.version = "0.0.1"
        receipt_mod.write(dest, receipt)

    assert main(["update"]) == 0
    assert "found 3 install(s)" in capsys.readouterr().out
    assert [receipt_mod.read(d).version for d in dests] == [__version__] * 3
    # Codex at user scope was never installed, so update did not create it.
    assert not registry.get("codex").dest("user", skill.name).exists()


def test_bare_update_with_nothing_installed(isolated_home, tmp_path, monkeypatch):
    from get_fsa_training_done.errors import NotInstalledError

    monkeypatch.chdir(tmp_path)
    with pytest.raises(NotInstalledError):
        main(["update"])
