"""Install, update, and uninstall — including the cases that risk losing work.

Parametrized over every registered skill via the `skill` fixture, so the day
a second skill registers, this whole lifecycle matrix runs against it too
with zero edits to this file.
"""

from __future__ import annotations

import json

import pytest

from fsa_trainer_skills import skills as skill_registry
from fsa_trainer_skills.__about__ import __version__
from fsa_trainer_skills.cli import main
from fsa_trainer_skills.install import receipt as receipt_mod
from fsa_trainer_skills.platforms import registry


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
    assert receipt.cli["invocation"][-2:] == ["-m", "fsa_trainer_skills"]
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
    assert "not installed by fsa-trainer-skills" in capsys.readouterr().out
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
    assert "no fsa-trainer-skills receipt" in capsys.readouterr().out
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
