"""One case per rule.

A documented rule that never fires teaches the model a constraint nothing holds
it to — and `references/structure.md` is generated from the same table, so the
prose would promise it too. Each case makes one edit to the clean module.
"""

from __future__ import annotations

from get_fsa_training_done.skills.material.core import rules

NOTE = "01_Relational_Modelling.md"
SECOND = "02_Querying.md"
LAB = "dbf_lab_01.md"
APPENDIX = "99_Appendix.md"


def test_the_shipped_module_is_clean(fired, module):
    """Everything else here is a deviation from this baseline."""
    assert fired(module) == set()


# --- One document ---------------------------------------------------------


def test_d01_a_filename_outside_the_convention_is_caught(fired, module):
    (module / NOTE).rename(module / "relational-modelling.md")
    assert "MAT-D01" in fired(module)


def test_d02_two_notes_claiming_one_index_are_caught(fired, module):
    (module / SECOND).rename(module / "01_Querying.md")
    assert "MAT-D02" in fired(module)


def test_d03_a_gap_in_the_indexes_warns(fired, module):
    (module / SECOND).rename(module / "04_Querying.md")
    assert "MAT-D03" in fired(module)


def test_d04_a_second_top_level_heading_is_caught(fired, module, edit):
    """A `#` used mid-file as a part divider — the commonest legacy defect."""
    edit(module, NOTE, "## 3. Keys", "# PART 2\n\n## 3. Keys")
    assert "MAT-D04" in fired(module)


def test_d04_a_title_below_the_first_line_is_caught(fired, module, edit):
    edit(module, NOTE, "# Relational Modelling\n", "\n# Relational Modelling\n")
    assert "MAT-D04" in fired(module)


def test_d05_yaml_front_matter_is_caught(fired, module, edit):
    edit(module, NOTE, "# Relational Modelling", "---\ntitle: x\n---\n\n# Relational Modelling")
    assert "MAT-D05" in fired(module)


def test_d06_a_missing_objectives_section_is_caught(fired, module, edit):
    edit(module, NOTE, "## 1. Objectives", "## 1. Introduction")
    assert "MAT-D06" in fired(module)


def test_d06_the_wrong_opening_sentence_is_caught(fired, module, edit):
    edit(module, NOTE, "After this unit, learners can:", "This unit covers:")
    assert "MAT-D06" in fired(module)


def test_d07_a_gap_in_the_section_numbers_is_caught(fired, module, edit):
    edit(module, NOTE, "## 3. Keys", "## 4. Keys")
    assert "MAT-D07" in fired(module)


def test_d08_a_note_with_no_knowledge_check_is_caught(fired, module, edit):
    edit(module, NOTE, "## 8. Knowledge Check", "## 8. Summary")
    assert "MAT-D08" in fired(module)


def test_d08_a_note_with_nowhere_to_go_next_is_caught(fired, module, edit):
    edit(module, NOTE, "## 9. Further Reading", "## 9. Appendix")
    assert "MAT-D08" in fired(module)


def test_d09_a_thin_knowledge_check_warns(fired, module, edit):
    body = "## 8. Knowledge Check\n\n1. One question only.\n\n## 9. Further Reading"
    edit(module, NOTE, "## 8. Knowledge Check", "@@")
    path = module / NOTE
    text = path.read_text(encoding="utf-8")
    head, _, tail = text.partition("@@")
    path.write_text(head + body + tail.split("## 9. Further Reading", 1)[1], encoding="utf-8")
    assert "MAT-D09" in fired(module)


def test_d10_an_untagged_fence_is_caught(fired, module, edit):
    edit(module, NOTE, "```sql\nCREATE TABLE book (", "```\nCREATE TABLE book (")
    assert "MAT-D10" in fired(module)


def test_d11_an_unknown_fence_language_warns(fired, module, edit):
    edit(module, NOTE, "```text", "```asciidoc")
    assert "MAT-D11" in fired(module)


def test_d12_a_link_to_a_missing_file_is_caught(fired, module, edit):
    edit(module, NOTE, "(00_Study_Guide_Handbook.md)", "(00_Missing.md)")
    assert "MAT-D12" in fired(module)


def test_d13_an_anchor_that_no_longer_exists_is_caught(fired, module, edit):
    """The appendix's deep links are the only ones in a module, and a renamed
    heading breaks them with nothing else to report it."""
    edit(module, SECOND, "# Querying\n", "# Querying Data\n")
    assert "MAT-D13" in fired(module)


def test_d14_a_chapter_with_no_next_link_is_caught(fired, module, verify):
    chapter = module / "05_Chapter.md"
    chapter.write_text(
        "# Chapter 5 · Indexes\n\n## Objective\n\nAfter this chapter, learners can:\n\n"
        "- Read a query plan.\n\n## 1. Plans\n\nProse.\n\n## Real-world use\n\nProse.\n\n"
        "## Self-check checklist\n\n- [ ] I can read a plan.\n",
        encoding="utf-8",
    )
    findings = {f["rule"] for f in verify(chapter, "--type", "chapter")["findings"]}
    assert "MAT-D14" in findings


def test_d15_a_self_check_list_without_task_items_is_caught(verify, tmp_path):
    chapter = tmp_path / "05_Chapter.md"
    chapter.write_text(
        "# Chapter 5 · Indexes\n\n## Objective\n\nAfter this chapter, learners can:\n\n"
        "- Read a query plan.\n\n## 1. Plans\n\nProse.\n\n## Real-world use\n\nProse.\n\n"
        "## Self-check checklist\n\n- I can read a plan.\n\n"
        "Next: [06_Next.md](06_Next.md) — more.\n",
        encoding="utf-8",
    )
    (tmp_path / "06_Next.md").write_text("# Next\n", encoding="utf-8")
    findings = {f["rule"] for f in verify(chapter, "--type", "chapter")["findings"]}
    assert "MAT-D15" in findings


def test_d16_vietnamese_outside_a_translation_warns(fired, module, edit):
    edit(module, NOTE, "An entity is a thing", "Một thực thể là một thứ")
    assert "MAT-D16" in fired(module)


def test_d16_a_translation_may_be_vietnamese(fired, module):
    translated = module / "01_Relational_Modelling_vn.md"
    translated.write_text(
        (module / NOTE)
        .read_text(encoding="utf-8")
        .replace("An entity is a thing", "Một thực thể là một thứ"),
        encoding="utf-8",
    )
    assert "MAT-D16" not in fired(translated)


def test_d17_a_lab_without_ordered_steps_is_caught(fired, module):
    """A lab whose steps are prose is an assignment brief in disguise."""
    path = module / LAB
    text = path.read_text(encoding="utf-8")
    head, _, tail = text.partition("## Steps")
    body = tail.split("## Acceptance", 1)[1]
    path.write_text(
        head + "## Steps\n\nModel the catalogue, then implement it.\n\n## Acceptance" + body,
        encoding="utf-8",
    )
    assert "MAT-D17" in fired(path)


def test_d17_a_lab_without_a_checkable_outcome_is_caught(fired, module):
    path = module / LAB
    text = path.read_text(encoding="utf-8")
    head, _, _ = text.partition("## Acceptance")
    path.write_text(
        head + "## Acceptance\n\nThe schema runs and the seed is idempotent.\n", "utf-8"
    )
    assert "MAT-D17" in fired(path)


def test_d18_a_lab_with_no_duration_warns(fired, module, edit):
    edit(module, LAB, "**Duration:** 90 min · ", "")
    assert "MAT-D18" in fired(module / LAB)


# --- Against the session plan --------------------------------------------


def test_c01_a_material_the_plan_names_but_which_is_missing(coverage_fired, module, plan_path):
    (module / LAB).unlink()
    assert "MAT-C01" in coverage_fired(plan_path, module)


def test_c02_a_material_no_session_uses_warns(coverage_fired, module, plan_path):
    (module / "03_Extra.md").write_text("# Extra\n", encoding="utf-8")
    assert "MAT-C02" in coverage_fired(plan_path, module)


def test_c03_a_material_that_ignores_its_sessions_objectives_warns(
    coverage_fired, module, plan_path, edit
):
    path = module / LAB
    path.write_text(path.read_text(encoding="utf-8").replace("DBF-K2", "DBF-K1"), "utf-8")
    assert "MAT-C03" in coverage_fired(plan_path, module)


def test_c04_an_objective_the_syllabus_does_not_define_warns(
    coverage_fired, module, plan_path, syllabus_path
):
    text = plan_path.read_text(encoding="utf-8").replace("DBF-K2", "DBF-K9")
    plan_path.write_text(text, encoding="utf-8")
    assert "MAT-C04" in coverage_fired(plan_path, module, "--syllabus", str(syllabus_path))


def test_the_shipped_module_covers_its_plan_exactly(coverage_fired, module, plan_path):
    assert coverage_fired(plan_path, module) == set()


def test_another_skills_files_are_never_reported_missing(module, plan_path, capsys):
    """The plan also names a quiz and an exam. They belong to the assessment
    skill, and reporting them here would send someone to write the wrong thing."""
    import json

    from get_fsa_training_done.cli import main

    capsys.readouterr()
    main(["material", "coverage", "--schedule", str(plan_path), "--dir", str(module), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["facts"]["owned by another skill"] == 2
    assert payload["findings"] == []


# --- Coverage of the rulebook --------------------------------------------


def test_every_rule_has_a_case_here():
    from pathlib import Path

    source = Path(__file__).read_text(encoding="utf-8")
    assert [rule.id for rule in rules.RULES if rule.id not in source] == []


def test_no_duplicate_rule_ids():
    ids = [rule.id for rule in rules.RULES]
    assert len(ids) == len(set(ids))
