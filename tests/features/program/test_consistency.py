"""Payload-shape gates specific to the `program` feature.

Cross-skill invariants — payload validity against Codex's rules, no duplicate
names, version sync, generated files current — live in the top-level
`tests/test_consistency.py`. These are the checks that only make sense here:
the example the model is pointed at must actually be exemplary, and the router
must reach the CLI it names.
"""

from __future__ import annotations

from get_fsa_training_done.features.program.core import rules, schedule
from get_fsa_training_done.skill import SKILL

FEATURE = SKILL.payload_dir / "references" / "program"


def payload_text(*parts: str) -> str:
    return (FEATURE.joinpath(*parts)).read_text(encoding="utf-8")


def test_the_shipped_example_programme_verifies_clean(fired):
    """The example is the model's picture of a correct programme.

    If it carries so much as a warning, every programme written from it
    inherits the same flaw — and the model has no way to tell.
    """
    assert fired(FEATURE / "examples" / "mini") == set()


def test_every_rule_id_appears_in_the_generated_reference():
    """`rules.md` is what the model reads when a finding names a rule."""
    text = payload_text("rules.md")
    assert [rule.id for rule in rules.RULES if rule.id not in text] == []


def test_every_delivery_type_is_documented():
    text = payload_text("schemas.md")
    assert [t for t in schedule.DELIVERY_TYPES if f"`{t}`" not in text] == []


def test_the_schedule_header_is_documented_verbatim():
    """The model writes this header by hand; a paraphrase in the docs produces
    a file that fails PRG-S01."""
    text = payload_text("schemas.md")
    assert ",".join(schedule.SCHEDULE_HEADER) in text


CAPSTONE = FEATURE / "examples" / "capstone" / "curriculum"


def test_the_shipped_capstone_example_verifies_clean(fired):
    """A project module graded by three sprint reviews and a final review.

    Its one chapter spans the three sprints on purpose, which is the case
    `--max-sessions-per-chapter inf` exists for; without it, that is the only
    finding.
    """
    assert fired(CAPSTONE, "--max-sessions-per-chapter", "inf") == set()
    assert fired(CAPSTONE) == {"PRG-S08"}
