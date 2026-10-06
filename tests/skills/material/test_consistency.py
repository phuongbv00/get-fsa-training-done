"""Payload-shape gates specific to the `material` skill."""

from __future__ import annotations

import re

from get_fsa_training_done.__about__ import CLI_NAME, PACKAGE_NAME
from get_fsa_training_done.install.receipt import RECEIPT_NAME
from get_fsa_training_done.skills.material import SKILL
from get_fsa_training_done.skills.material.core import grammar, rules


def payload_text(*parts: str) -> str:
    return SKILL.payload_dir.joinpath(*parts).read_text(encoding="utf-8")


def test_the_shipped_example_module_verifies_clean(fired):
    """The example is the model's picture of a correct module.

    A warning here is inherited by every document written from it, and the
    model has no way to tell.
    """
    assert fired(SKILL.payload_dir / "references" / "examples" / "mini") == set()


def test_the_shipped_example_covers_its_session_plan(coverage_fired):
    from .conftest import MINI, PLAN

    assert coverage_fired(PLAN, MINI) == set()


def test_the_router_links_every_workflow_file():
    router = payload_text("SKILL.md")
    unreachable = [
        path.relative_to(SKILL.payload_dir).as_posix()
        for path in sorted((SKILL.payload_dir / "references" / "workflows").rglob("*.md"))
        if path.relative_to(SKILL.payload_dir).as_posix() not in router
    ]
    assert unreachable == []


def test_references_named_by_the_payload_all_exist():
    pattern = re.compile(r"`(references/[A-Za-z0-9_./-]+)`")
    missing = []
    for path in sorted(SKILL.payload_dir.rglob("*.md")):
        for match in pattern.finditer(path.read_text(encoding="utf-8")):
            target = SKILL.payload_dir / match.group(1)
            if not target.exists() and not str(target).endswith("/"):
                missing.append(f"{path.relative_to(SKILL.payload_dir)} -> {match.group(1)}")
    assert missing == []


def test_the_router_names_the_real_cli_and_receipt():
    router = payload_text("SKILL.md")
    section = router[router.index("## Resolving the CLI") : router.index("## Step 1")]
    assert RECEIPT_NAME in section
    assert f"{CLI_NAME} --version" in section
    assert f"pip install {PACKAGE_NAME}" in section
    assert f"npm install -g {PACKAGE_NAME}" in section


def test_every_rule_id_appears_in_the_generated_reference():
    text = payload_text("references", "structure.md")
    assert [rule.id for rule in rules.RULES if rule.id not in text] == []


def test_every_template_is_documented():
    text = payload_text("references", "structure.md")
    assert [t.title for t in grammar.TEMPLATES if t.title not in text] == []


def test_every_fence_language_is_documented():
    """The model picks a tag from this list; one missing from the docs is one
    it will not use, and one it invents becomes a warning."""
    text = payload_text("references", "structure.md")
    assert [name for name in grammar.FENCE_LANGUAGES if f"`{name}`" not in text] == []


def test_every_shipped_template_parses_as_the_kind_it_names():
    """A skeleton the checker would reject teaches the wrong shape."""
    from get_fsa_training_done.skills.material.core import notes

    for name, key in (
        ("lecture_note.md", "unit"),
        ("lab_guide.md", "lab"),
        ("handbook.md", "handbook"),
        ("appendix.md", "appendix"),
    ):
        note = notes.parse(SKILL.payload_dir / "references" / "templates" / name)
        template = grammar.BY_KEY[key]
        assert note.headings and note.headings[0].level == 1, name
        for slot in template.slots:
            if slot.required:
                assert note.section_named(slot.names) is not None, f"{name}: {slot.label}"
