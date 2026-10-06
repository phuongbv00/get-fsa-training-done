"""The sprint pack is derived from the spec, and stays derived.

The whole point of generating it is that the handout a team reads, the section
`verify` checks, and the caps the rubric applies cannot disagree. A test that
only checked the files appear would not defend that.
"""

from __future__ import annotations

import csv

import pytest

from get_fsa_training_done.errors import UsageError
from get_fsa_training_done.skills.assessment.core import sprintkit
from get_fsa_training_done.skills.assessment.core.verify import CheckResult, capstone

from .conftest import FIXTURES

#: The Drive root the canonical fixture spec was generated with.
FIXTURE_DRIVE_ROOT = "MKP-F26"

EN = sprintkit.LOCALES["en"]
VI = sprintkit.LOCALES["vi"]


@pytest.fixture
def project(capstone_trio):
    _, spec, _ = capstone_trio
    return sprintkit.read_project(spec)


def test_the_kit_writes_every_file(project, tmp_path):
    written = sprintkit.write_kit(project, tmp_path / "kit", FIXTURE_DRIVE_ROOT, EN)
    assert sorted(path.name for path in written) == [
        "SUBMISSION_GUIDE.md",
        "backlog_template.csv",
        "spec_sprint_checkpoint.md",
        "sprint_review_template.md",
    ]
    assert all(path.stat().st_size > 0 for path in written)


def test_the_calendar_is_read_from_the_spec(project):
    assert [sprint.number for sprint in project.sprints] == [1, 2, 3]
    assert str(project.sprints[0].start) == "2026-09-01"
    assert project.sprints[2].deliverables == ("D04", "D05")
    assert project.code == "FR_MKP_PRJ_01"


def test_the_handout_carries_the_real_deadlines_and_deliverables(project):
    text = sprintkit.handout(project, FIXTURE_DRIVE_ROOT, EN)
    assert f"2026-10-12 {sprintkit.DEADLINE_TIME}" in text
    assert "D04 Source Code" in text
    assert f"{FIXTURE_DRIVE_ROOT}/<TEAM>/Sprint 3/" in text
    # A tick-box line per gate per sprint, with the sprint number substituted.
    assert "- [ ] **G2** `git tag -a sprint-3` created on the default branch" in text
    assert "{n}" not in text


def test_the_handout_has_a_checklist_block_for_every_sprint(project):
    text = sprintkit.handout(project, FIXTURE_DRIVE_ROOT, EN)
    for sprint in project.sprints:
        assert f"### Sprint {sprint.number} — due {sprint.end}" in text


def test_the_generated_checkpoint_section_is_what_the_spec_holds(project):
    """The fixture spec was written by `--update-spec`; regenerating must be a no-op."""
    spec_text = (FIXTURES / "capstone" / "mkp_capstone_project_01_spec.md").read_text(
        encoding="utf-8"
    )
    generated = sprintkit.checkpoint_section(project, FIXTURE_DRIVE_ROOT, EN)
    assert generated.strip() in spec_text


def test_update_spec_is_idempotent(capstone_trio, project):
    _, spec, _ = capstone_trio
    before = spec.read_text(encoding="utf-8")
    sprintkit.update_spec(spec, project, FIXTURE_DRIVE_ROOT, EN)
    assert spec.read_text(encoding="utf-8") == before


def test_the_regenerated_spec_still_verifies(capstone_trio, project):
    brief, spec, rubric = capstone_trio
    sprintkit.update_spec(spec, project, FIXTURE_DRIVE_ROOT, EN)
    result = CheckResult()
    capstone.verify(
        brief_path=str(brief), spec_path=str(spec), rubric_path=str(rubric), result=result
    )
    assert result.errors == []


def test_update_spec_without_the_heading_is_a_usage_error(capstone_trio, project):
    _, spec, _ = capstone_trio
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("## Sprint checkpoint", "## Notes"),
        encoding="utf-8",
    )
    with pytest.raises(UsageError, match="no '## Sprint checkpoint' heading"):
        sprintkit.update_spec(spec, project, FIXTURE_DRIVE_ROOT, EN)


def test_a_broken_calendar_refuses_to_generate(capstone_trio):
    _, spec, _ = capstone_trio
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("| 1 | 2026-09-01 |", "| 1 | 01/09/2026 |"),
        encoding="utf-8",
    )
    with pytest.raises(UsageError, match="unusable sprint calendar"):
        sprintkit.read_project(spec)


def test_the_backlog_template_header_is_the_frozen_column_order(project, tmp_path):
    path = tmp_path / "backlog_template.csv"
    sprintkit.write_backlog_template(path)
    rows = list(csv.reader(path.read_text(encoding="utf-8-sig").splitlines()))
    assert tuple(rows[0]) == sprintkit.BACKLOG_COLUMNS
    # Every example row uses a status the checklist actually allows.
    for row in rows[1:]:
        assert row[4] in sprintkit.BACKLOG_STATUSES


def test_gate_ids_match_the_verifier(project):
    assert sprintkit.gate_ids() == tuple(capstone.CHECKPOINT_GATES)


def test_the_kit_names_every_deliverable_the_rubric_scores(project):
    text = sprintkit.handout(project, FIXTURE_DRIVE_ROOT, EN)
    for deliverable, name in capstone.DELIVERABLE_NAMES.items():
        assert f"{deliverable} {name}" in text


# --------------------------------------------------------------------------- #
# Other languages on request; English is the default
# --------------------------------------------------------------------------- #


def test_english_is_the_default_locale():
    assert sprintkit.DEFAULT_LANGUAGE == "en"
    assert sprintkit.LOCALES[sprintkit.DEFAULT_LANGUAGE] is EN


@pytest.mark.parametrize("locale", list(sprintkit.LOCALES.values()), ids=lambda loc: loc.code)
def test_every_locale_agrees_with_the_verifier_on_gate_ids(locale):
    assert sprintkit.gate_ids(locale) == tuple(capstone.CHECKPOINT_GATES)


@pytest.mark.parametrize("locale", list(sprintkit.LOCALES.values()), ids=lambda loc: loc.code)
def test_every_locale_leaves_no_placeholder_unfilled(project, locale):
    """A `{n}` that survives into the handout is a checklist line nobody can tick."""
    for text in (
        sprintkit.handout(project, FIXTURE_DRIVE_ROOT, locale),
        sprintkit.checkpoint_section(project, FIXTURE_DRIVE_ROOT, locale),
    ):
        for placeholder in ("{n}", "{drive_root}", "{deadline}", "{gates}", "{schedule}"):
            assert placeholder not in text


@pytest.mark.parametrize("locale", list(sprintkit.LOCALES.values()), ids=lambda loc: loc.code)
def test_every_locale_carries_the_same_facts(project, locale):
    """Prose is translated; dates, paths, ids, and filenames are not."""
    text = sprintkit.handout(project, FIXTURE_DRIVE_ROOT, locale)
    for fact in (
        "2026-10-12",
        "D04 Source Code",
        f"{FIXTURE_DRIVE_ROOT}/<TEAM>/Sprint 3/",
        "git tag -a sprint-3",
        "backlog_sprint1_close.csv",
    ):
        assert fact in text
    for gate in capstone.CHECKPOINT_GATES:
        assert f"**{gate}**" in text


def test_a_vietnamese_spec_section_still_verifies(capstone_trio, project):
    """The gate ids are language-neutral, so `verify` does not care which locale ran."""
    brief, spec, rubric = capstone_trio
    sprintkit.update_spec(spec, project, FIXTURE_DRIVE_ROOT, VI)
    result = CheckResult()
    capstone.verify(
        brief_path=str(brief), spec_path=str(spec), rubric_path=str(rubric), result=result
    )
    assert result.errors == []


def test_an_unsupported_language_is_a_usage_error():
    with pytest.raises(UsageError, match="unsupported --lang"):
        sprintkit.locale_for("fr")
