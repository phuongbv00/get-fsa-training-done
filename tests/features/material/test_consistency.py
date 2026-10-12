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


def test_every_kind_is_documented():
    text = payload_text("structure.md")
    assert [k.title for k in grammar.KINDS if k.title not in text] == []


def test_every_part_is_documented():
    text = payload_text("structure.md")
    missing = [
        f"{kind.key}.{part.key}"
        for kind in grammar.KINDS
        for part in kind.parts
        if f"`{part.key}`" not in text
    ]
    assert missing == []


def test_every_layout_and_slot_is_documented():
    from get_fsa_training_done.features.material.core import layouts

    text = payload_text("layouts.md")
    missing = [layout.name for layout in layouts.LAYOUTS if f"### `{layout.name}`" not in text]
    missing += [
        f"{layout.name}.{slot.name}"
        for layout in layouts.LAYOUTS
        for slot in layout.slots
        if f"`{slot.name}`" not in text
    ]
    assert missing == []


def test_every_fence_language_is_documented():
    """The model picks a tag from this list; one missing from the docs is one
    it will not use, and one it invents becomes a warning."""
    text = payload_text("structure.md")
    assert [name for name in grammar.CODE_LANGUAGES if f"`{name}`" not in text] == []


def test_every_shipped_template_parses_as_the_kind_it_names(tmp_path, capsys):
    """A skeleton the checker would reject teaches the wrong shape.

    Each template is checked under a module filename so its kind is inferred, and
    only placeholder links and objective coverage may differ from a real file.
    """
    import json
    import shutil

    from get_fsa_training_done.cli import main

    names = {
        "deck.html": "01_Topic.deck.html",
        "lecture_note.html": "subj_lecture_note.html",
        "lab_guide.html": "subj_lab_01.html",
        "handbook.html": "00_Study_Guide_Handbook.html",
        "appendix.html": "99_Appendix.html",
    }
    for template, name in names.items():
        shutil.copy(FEATURE / "templates" / template, tmp_path / name)
    capsys.readouterr()
    main(["material", "verify", str(tmp_path), "--json"])
    findings = json.loads(capsys.readouterr().out)["findings"]
    errors = [
        f"{f['rule']} {f['where']}: {f['message']}"
        for f in findings
        if f["severity"] == "error" and f["rule"] not in ("MAT-D12", "MAT-D29")
    ]
    # The appendix's map is empty until `derive appendix` fills it.
    errors += [
        f"{f['rule']} {f['where']}: {f['message']}"
        for f in findings
        if f["rule"] == "MAT-D29" and f["where"] != "99_Appendix.html"
    ]
    assert errors == []


#: Every task that creates a document. Each must open on the outline gate.
WRITING_TASKS = (
    "write_deck.md",
    "write_lecture.md",
    "write_lab.md",
    "write_handbook.md",
    "write_worksheet.md",
    "derive_appendix.md",
)
OUTLINE_TASK = "references/material/tasks/propose_outline.md"


def test_every_writing_task_opens_on_the_outline_gate():
    """Nothing is written before its outline is approved — and the gate is the
    first step, so a model reading the task top-down cannot skip past it."""
    missing = []
    for name in WRITING_TASKS:
        text = payload_text("tasks", name)
        steps = text.split("## Steps", 1)[1]
        first_step = steps.split("\n2. ", 1)[0]
        if "Outline first" not in first_step or OUTLINE_TASK not in first_step:
            missing.append(name)
    assert missing == []


def test_the_outline_gate_is_a_standing_rule_and_in_every_workflow():
    assert OUTLINE_TASK in payload_text("overview.md")
    for workflow in ("module_pack.md", "fill_gaps.md"):
        text = payload_text("workflows", workflow)
        assert OUTLINE_TASK in text, workflow
        # ...and it comes before the first writing task.
        assert text.index(OUTLINE_TASK) < text.index("tasks/write_"), workflow
