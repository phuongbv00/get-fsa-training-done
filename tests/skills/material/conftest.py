"""Fixtures for the material skill's tests.

The clean module ships in the payload — the example the model reads and the
fixture the tests trust are the same bytes — and every failing case is a copy of
it with one targeted edit.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from get_fsa_training_done.cli import main
from get_fsa_training_done.skills.material import SKILL

EXAMPLES = SKILL.payload_dir / "references" / "examples"
MINI = EXAMPLES / "mini"
PLAN = EXAMPLES / "plan" / "AA_FR_TT_DBF_ScheduleDetail.csv"
SYLLABUS = EXAMPLES / "plan" / "AA_FR_TT_DBF_Syllabus.md"


@pytest.fixture(autouse=True)
def no_venv(monkeypatch):
    """Keep worker commands in-process; otherwise each call builds a venv."""
    monkeypatch.setenv("GET_FSA_TRAINING_DONE_NO_VENV", "1")


@pytest.fixture
def module(tmp_path):
    """A writable copy of the clean module, with its session plan beside it."""
    target = tmp_path / "Lectures"
    shutil.copytree(MINI, target)
    plan = tmp_path / "plan"
    plan.mkdir()
    shutil.copy(PLAN, plan / PLAN.name)
    shutil.copy(SYLLABUS, plan / SYLLABUS.name)
    return target


@pytest.fixture
def plan_path(module):
    return module.parent / "plan" / PLAN.name


@pytest.fixture
def syllabus_path(module):
    return module.parent / "plan" / SYLLABUS.name


@pytest.fixture
def verify(capsys):
    def run(*args: str) -> dict:
        capsys.readouterr()
        main(["material", "verify", *[str(a) for a in args], "--json"])
        return json.loads(capsys.readouterr().out)

    return run


@pytest.fixture
def fired(verify):
    def run(*args) -> set[str]:
        return {f["rule"] for f in verify(*args)["findings"]}

    return run


@pytest.fixture
def coverage_fired(capsys):
    def run(schedule: Path, directory: Path, *extra: str) -> set[str]:
        capsys.readouterr()
        main(
            [
                "material",
                "coverage",
                "--schedule",
                str(schedule),
                "--dir",
                str(directory),
                "--json",
                *extra,
            ]
        )
        payload = json.loads(capsys.readouterr().out)
        return {f["rule"] for f in payload["findings"]}

    return run


@pytest.fixture
def edit():
    def apply(root: Path, name: str, old: str, new: str, count: int = 1) -> Path:
        path = root / name
        text = path.read_text(encoding="utf-8")
        assert text.count(old) >= 1, f"{name} does not contain {old!r}"
        path.write_text(text.replace(old, new, count), encoding="utf-8")
        return path

    return apply
