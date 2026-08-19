"""Gates that stop the repo shipping something internally inconsistent
across the skill registry.

The version lives in several files and the `assess` skill's level table lives
in two — one for the CLI to read and one for the model to read. Drift between
them is invisible at runtime: a workflow would calibrate to numbers the
verifier does not check against. These run in CI for that reason.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from fsa_trainer_skills import skills as skill_registry
from fsa_trainer_skills.platforms import registry
from fsa_trainer_skills.skillmeta import read_skill_frontmatter

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


@pytest.mark.skipif(not (SCRIPTS / "sync_version.py").exists(), reason="script missing")
def test_version_is_consistent_across_files():
    result = run_script("sync_version.py", "--check")
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(not (SCRIPTS / "assess" / "gen_levels_md.py").exists(), reason="script missing")
def test_levels_markdown_matches_the_python_table():
    result = run_script("assess/gen_levels_md.py", "--check")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("skill", skill_registry.all_skills(), ids=lambda s: s.namespace)
def test_every_skill_payload_satisfies_codex_rules(skill):
    problems = registry.get("codex").validate(skill.payload_dir)
    assert [str(p) for p in problems if p.fatal] == []


@pytest.mark.parametrize("skill", skill_registry.all_skills(), ids=lambda s: s.namespace)
def test_every_skill_description_has_no_angle_brackets(skill):
    front = read_skill_frontmatter(skill.payload_dir / "SKILL.md")
    assert "<" not in front["description"] and ">" not in front["description"]
    assert len(front["description"]) <= 1024


def test_no_duplicate_skill_names_or_namespaces():
    all_skills = skill_registry.all_skills()
    assert len({s.name for s in all_skills}) == len(all_skills)
    assert len({s.namespace for s in all_skills}) == len(all_skills)
