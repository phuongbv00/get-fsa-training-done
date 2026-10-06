"""Payload-shape gates specific to the `material` feature."""

from __future__ import annotations

from get_fsa_training_done.features.material.core import grammar, rules
from get_fsa_training_done.skill import SKILL

FEATURE = SKILL.payload_dir / "references" / "material"


def payload_text(*parts: str) -> str:
    return FEATURE.joinpath(*parts).read_text(encoding="utf-8")


def test_the_shipped_example_module_verifies_clean(fired):
    """The example is the model's picture of a correct module.

    A warning here is inherited by every document written from it, and the
    model has no way to tell.
    """
    assert fired(FEATURE / "examples" / "mini") == set()


def test_the_shipped_example_covers_its_session_plan(coverage_fired):
    from .conftest import MINI, PLAN

    assert coverage_fired(PLAN, MINI) == set()


def test_every_rule_id_appears_in_the_generated_reference():
    text = payload_text("structure.md")
    assert [rule.id for rule in rules.RULES if rule.id not in text] == []


def test_every_template_is_documented():
    text = payload_text("structure.md")
    assert [t.title for t in grammar.TEMPLATES if t.title not in text] == []


def test_every_fence_language_is_documented():
    """The model picks a tag from this list; one missing from the docs is one
    it will not use, and one it invents becomes a warning."""
    text = payload_text("structure.md")
    assert [name for name in grammar.FENCE_LANGUAGES if f"`{name}`" not in text] == []


def test_every_shipped_template_parses_as_the_kind_it_names():
    """A skeleton the checker would reject teaches the wrong shape."""
    from get_fsa_training_done.features.material.core import notes

    for name, key in (
        ("lecture_note.md", "unit"),
        ("lab_guide.md", "lab"),
        ("handbook.md", "handbook"),
        ("appendix.md", "appendix"),
    ):
        note = notes.parse(FEATURE / "templates" / name)
        template = grammar.BY_KEY[key]
        assert note.headings and note.headings[0].level == 1, name
        for slot in template.slots:
            if slot.required:
                assert note.section_named(slot.names) is not None, f"{name}: {slot.label}"
