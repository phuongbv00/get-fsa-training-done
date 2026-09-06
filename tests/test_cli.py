"""Dispatch: lifecycle verbs run in place, skill verbs reach their worker."""

from __future__ import annotations

import json

import pytest

from fsa_trainer_skills import cli
from fsa_trainer_skills.errors import UsageError


@pytest.fixture(autouse=True)
def no_venv(monkeypatch):
    """Worker commands re-exec into the managed venv; keep them in-process here."""
    monkeypatch.setenv("FSA_TRAINER_SKILLS_NO_VENV", "1")


def test_a_skill_verb_reaches_its_worker(capsys):
    assert cli.main(["assess", "levels", "show", "--level", "UP_SKILL:mid", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["id"] == "UP_SKILL:mid"


def test_the_level_flag_rejects_a_missing_band():
    with pytest.raises(UsageError, match="needs a band"):
        cli.main(["assess", "levels", "show", "--level", "UP_SKILL"])


def test_doctor_reports_every_dependency_group(capsys):
    from fsa_trainer_skills.envmgr import stamp

    cli.main(["doctor", "--json"])
    report = json.loads(capsys.readouterr().out)
    assert set(report["environments"]) == set(stamp.GROUPS)
