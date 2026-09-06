"""The level calibration table.

These numbers drive every workflow's defaults, so the invariants that make them
usable — percentages that sum to 100, counts that sum to the requested total —
are asserted rather than assumed.
"""

from __future__ import annotations

import pytest

from fsa_trainer_skills.skills.assess.core import levels


def test_every_level_has_coherent_percentages():
    for level in levels.LEVELS:
        assert sum(level.bloom.values()) == 100, level.id
        assert sum(level.difficulty.values()) == 100, level.id


def test_the_expected_eight_levels_exist():
    ids = {level.id for level in levels.LEVELS}
    assert ids == {
        "CPL",
        "FR",
        "UP_SKILL:junior",
        "UP_SKILL:mid",
        "UP_SKILL:senior",
        "RE_SKILL:junior",
        "RE_SKILL:mid",
        "RE_SKILL:senior",
    }


def test_resolve_accepts_aliases():
    assert levels.resolve("intern").key == "CPL"
    assert levels.resolve("fresher").key == "FR"
    assert levels.resolve("up-skill", "mid").band == "mid"


def test_resolve_accepts_the_band_in_the_key():
    """`--level UP_SKILL:mid` — one flag names any level, so a workflow template
    does not need a second placeholder that CPL and FR must leave out."""
    assert levels.resolve("UP_SKILL:mid").id == "UP_SKILL:mid"
    assert levels.resolve("re-skill:Senior").band == "senior"


def test_a_banded_level_requires_a_band():
    with pytest.raises(levels.UnknownLevel, match="needs a band"):
        levels.resolve("UP_SKILL")


def test_an_unbanded_level_rejects_a_band():
    with pytest.raises(levels.UnknownLevel, match="no bands"):
        levels.resolve("FR", "mid")


def test_unknown_level_names_the_alternatives():
    with pytest.raises(levels.UnknownLevel, match="CPL"):
        levels.resolve("PRINCIPAL")


@pytest.mark.parametrize("total", [10, 40, 80, 37])
def test_counts_always_sum_to_the_requested_total(total):
    """Largest-remainder allocation, so rounding never loses or invents a question."""
    for level in levels.LEVELS:
        counts = levels.counts_for(level, total)
        assert sum(counts["bloom"].values()) == total, (level.id, total)
        assert sum(counts["difficulty"].values()) == total, (level.id, total)


def test_difficulty_rises_with_seniority():
    def hard(key, band):
        return levels.resolve(key, band).difficulty["Hard"]

    assert hard("CPL", None) < hard("FR", None)
    assert hard("FR", None) < hard("UP_SKILL", "junior")
    assert hard("UP_SKILL", "junior") < hard("UP_SKILL", "mid")
    assert hard("UP_SKILL", "mid") < hard("UP_SKILL", "senior")


def test_upskill_hides_mechanisms_and_reskill_names_them():
    """RE_SKILL candidates are new to the stack by definition, so naming the
    mechanism is information they legitimately need rather than a giveaway."""
    assert levels.resolve("UP_SKILL", "junior").may_name_mechanism is False
    assert levels.resolve("RE_SKILL", "junior").may_name_mechanism is True


def test_quiz_timing_is_the_same_at_every_level():
    for level in levels.LEVELS:
        assert levels.time_map_for(level, "quiz") == levels.QUIZ_TIME_MAP
