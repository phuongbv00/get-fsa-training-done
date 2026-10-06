"""Install, update, and uninstall — including the cases that risk losing work.

Parametrized over every registered skill via the `skill` fixture, so the day
a second skill registers, this whole lifecycle matrix runs against it too
with zero edits to this file.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from get_fsa_training_done import skills as skill_registry
from get_fsa_training_done.__about__ import __version__
from get_fsa_training_done.cli import main
from get_fsa_training_done.install import receipt as receipt_mod
from get_fsa_training_done.platforms import registry


@pytest.fixture(params=skill_registry.all_skills(), ids=lambda s: s.namespace)
def skill(request):
    return request.param


def dest_for(skill, platform: str, home=None) -> object:
    return registry.get(platform).dest("user", skill.name)


def test_install_creates_receipt_and_files(isolated_home, skill):
    args = ["--skill", skill.namespace, "--platform", "claude", "--no-prewarm"]
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
    args = ["--skill", skill.namespace, "--platform", "claude", "--no-prewarm"]
    main(["install", *args])
    capsys.readouterr()
    assert main(["install", *args]) == 0
    assert "already installed" in capsys.readouterr().out


def test_install_refuses_an_unmanaged_destination(isolated_home, skill, capsys):
    dest = dest_for(skill, "claude")
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("someone else's skill", encoding="utf-8")

    args = ["--skill", skill.namespace, "--platform", "claude", "--no-prewarm"]
    assert main(["install", *args]) == 1
    assert "not installed by get-fsa-training-done" in capsys.readouterr().out
    assert (dest / "SKILL.md").read_text(encoding="utf-8") == "someone else's skill"


def test_force_adopts_an_unmanaged_destination(isolated_home, skill):
    dest = dest_for(skill, "claude")
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("someone else's skill", encoding="utf-8")

    args = ["--skill", skill.namespace, "--platform", "claude", "--force", "--no-prewarm"]
    assert main(["install", *args]) == 0
    assert skill.name in (dest / "SKILL.md").read_text(encoding="utf-8")
    assert (dest / "SKILL.md.bak").is_file()


def test_dry_run_writes_nothing(isolated_home, skill):
    args = ["--skill", skill.namespace, "--platform", "claude", "--dry-run"]
    assert main(["install", *args]) == 0
    assert not dest_for(skill, "claude").exists()


def test_update_never_overwrites_a_user_edit(isolated_home, skill):
    base = ["--skill", skill.namespace, "--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    dest = dest_for(skill, "claude")
    edited = dest / "SKILL.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nmy note\n", encoding="utf-8")

    assert main(["update", *base]) == 0
    assert "my note" in edited.read_text(encoding="utf-8")
    assert (dest / "SKILL.md.new").is_file()


def test_a_conflicted_file_is_not_claimed_by_the_receipt(isolated_home, skill):
    """Otherwise uninstall would delete content the user wrote."""
    base = ["--skill", skill.namespace, "--platform", "claude"]
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
    base = ["--skill", skill.namespace, "--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    dest = dest_for(skill, "claude")
    assert main(["uninstall", *base]) == 0
    assert not dest.exists()


def test_uninstall_keeps_files_it_did_not_write(isolated_home, skill):
    base = ["--skill", skill.namespace, "--platform", "claude"]
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

    args = ["--skill", skill.namespace, "--platform", "claude"]
    assert main(["uninstall", *args]) == 1
    assert "no get-fsa-training-done receipt" in capsys.readouterr().out
    assert (dest / "SKILL.md").is_file()


def test_update_check_reports_up_to_date(isolated_home, skill):
    base = ["--skill", skill.namespace, "--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    assert main(["update", *base, "--check"]) == 0


def test_update_check_flags_an_older_install(isolated_home, skill):
    base = ["--skill", skill.namespace, "--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    dest = dest_for(skill, "claude")
    receipt = receipt_mod.read(dest)
    receipt.version = "0.0.1"
    receipt_mod.write(dest, receipt)
    assert main(["update", *base, "--check"]) == 1


@pytest.mark.parametrize("platform", ["claude", "codex"])
@pytest.mark.parametrize("scope", ["user", "project"])
def test_every_target_round_trips(isolated_home, tmp_path, skill, platform, scope):
    args = ["--skill", skill.namespace, "--platform", platform, "--scope", scope]
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
    base = ["--skill", skill.namespace, "--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    capsys.readouterr()
    assert main(["status", "--skill", skill.namespace, "--json"]) == 0
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
    base = ["--skill", skill.namespace, "--platform", "claude"]
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
    base = ["--skill", skill.namespace, "--platform", "claude"]
    main(["install", *base, "--no-prewarm"])
    main(["install", *base, "--scope", "project", "--project-root", str(project), "--no-prewarm"])
    capsys.readouterr()

    assert main(["status", *base, "--project-root", str(project), "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)["installs"]

    assert {row["scope"] for row in rows} == {"user", "project"}


# --- Legacy-name cleanup -------------------------------------------------
#
# Renaming a skill changes its install directory, orphaning the old one. The
# orphan is not inert: hosts load every directory under `skills/`, so a stale
# copy keeps advertising the same triggers and the agent sees two skills
# competing for one request. These cover the cleanup and, just as importantly,
# the directories it must refuse to touch.

LEGACY = "legacy-old-name"


@pytest.fixture
def renamed(skill, monkeypatch):
    """`skill`, as if it had previously been installed under another name.

    `Skill` is frozen, and the lifecycle commands look the skill up in the
    registry rather than taking one as an argument, so the copy has to go into
    the registry for the command under test to see it.
    """
    renamed_skill = dataclasses.replace(skill, previous_names=(LEGACY,))
    monkeypatch.setitem(skill_registry._SKILLS, skill.namespace, renamed_skill)
    return renamed_skill


def install_as(skill, name: str) -> object:
    """Put a real, receipted install at `name` — what the old version left."""
    assert (
        main(
            [
                "install",
                "--skill",
                skill.namespace,
                "--platform",
                "claude",
                "--name",
                name,
                "--no-prewarm",
            ]
        )
        == 0
    )
    return registry.get("claude").dest("user", name)


def test_install_clears_an_install_under_a_previous_name(isolated_home, renamed, capsys):
    legacy_dest = install_as(renamed, LEGACY)
    assert (legacy_dest / "SKILL.md").is_file()
    capsys.readouterr()

    assert (
        main(["install", "--skill", renamed.namespace, "--platform", "claude", "--no-prewarm"]) == 0
    )

    assert "removed the superseded" in capsys.readouterr().out
    assert not legacy_dest.exists()
    assert (dest_for(renamed, "claude") / "SKILL.md").is_file()


def test_update_clears_an_install_under_a_previous_name(isolated_home, renamed, capsys):
    legacy_dest = install_as(renamed, LEGACY)
    main(["install", "--skill", renamed.namespace, "--platform", "claude", "--no-prewarm"])
    # Put it back, so `update` is the command that has to notice it.
    legacy_dest = install_as(renamed, LEGACY)
    capsys.readouterr()

    assert main(["update", "--skill", renamed.namespace, "--platform", "claude"]) == 0
    assert not legacy_dest.exists()


def test_update_check_clears_nothing(isolated_home, renamed):
    legacy_dest = install_as(renamed, LEGACY)
    main(["install", "--skill", renamed.namespace, "--platform", "claude", "--no-prewarm"])
    legacy_dest = install_as(renamed, LEGACY)

    main(["update", "--skill", renamed.namespace, "--platform", "claude", "--check"])
    assert (legacy_dest / "SKILL.md").is_file()


def test_dry_run_clears_nothing(isolated_home, renamed, capsys):
    legacy_dest = install_as(renamed, LEGACY)
    capsys.readouterr()

    main(
        [
            "install",
            "--skill",
            renamed.namespace,
            "--platform",
            "claude",
            "--dry-run",
            "--no-prewarm",
        ]
    )

    assert "would remove the superseded" in capsys.readouterr().out
    assert (legacy_dest / "SKILL.md").is_file()


def test_legacy_cleanup_keeps_a_file_you_edited(isolated_home, renamed, capsys):
    legacy_dest = install_as(renamed, LEGACY)
    edited = legacy_dest / "SKILL.md"
    edited.write_text("my own notes", encoding="utf-8")
    capsys.readouterr()

    main(["install", "--skill", renamed.namespace, "--platform", "claude", "--no-prewarm"])

    assert "kept 1 file(s) you had modified" in capsys.readouterr().out
    assert edited.read_text(encoding="utf-8") == "my own notes"


def test_legacy_cleanup_ignores_a_directory_we_did_not_install(isolated_home, renamed):
    """No receipt means it is not ours, whatever it is called."""
    stranger = registry.get("claude").dest("user", LEGACY)
    stranger.mkdir(parents=True)
    (stranger / "SKILL.md").write_text("someone else's skill", encoding="utf-8")

    main(["install", "--skill", renamed.namespace, "--platform", "claude", "--no-prewarm"])

    assert (stranger / "SKILL.md").read_text(encoding="utf-8") == "someone else's skill"


def test_legacy_cleanup_ignores_a_receipt_naming_another_skill(isolated_home, renamed):
    """A receipt is only licence to delete when it names the name we expected."""
    legacy_dest = install_as(renamed, LEGACY)
    receipt = receipt_mod.read(legacy_dest)
    receipt.skill_name = "something-else"
    receipt_mod.write(legacy_dest, receipt)

    main(["install", "--skill", renamed.namespace, "--platform", "claude", "--no-prewarm"])

    assert (legacy_dest / "SKILL.md").is_file()


def test_status_reports_a_superseded_install_with_no_current_one(isolated_home, renamed, capsys):
    """The case that matters most: old name present, new name absent.

    An earlier version of this check only looked for legacy directories beside
    an install that already existed, so the one state a user actually upgrades
    from reported "No installs found" while the stale copy kept loading.
    """
    install_as(renamed, LEGACY)
    capsys.readouterr()

    assert main(["status", "--skill", renamed.namespace, "--platform", "claude"]) == 0
    out = capsys.readouterr().out
    assert "superseded install" in out
    assert LEGACY in out
    # `update` refuses when nothing is installed under the new name.
    assert "install --skill" in out


def test_status_json_lists_superseded_installs(isolated_home, renamed, capsys):
    install_as(renamed, LEGACY)
    capsys.readouterr()

    main(["status", "--skill", renamed.namespace, "--platform", "claude", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert [row["previous_name"] for row in payload["superseded"]] == [LEGACY]
