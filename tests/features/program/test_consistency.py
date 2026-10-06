"""Payload-shape gates specific to the `program` skill.

Cross-skill invariants — payload validity against Codex's rules, no duplicate
names, version sync, generated files current — live in the top-level
`tests/test_consistency.py`. These are the checks that only make sense here:
the example the model is pointed at must actually be exemplary, and the router
must reach the CLI it names.
"""

from __future__ import annotations

import re

from get_fsa_training_done.__about__ import CLI_NAME, PACKAGE_NAME
from get_fsa_training_done.features.program import SKILL
from get_fsa_training_done.features.program.core import rules, schedule
from get_fsa_training_done.lifecycle.install.receipt import RECEIPT_NAME


def payload_text(*parts: str) -> str:
    return (SKILL.payload_dir.joinpath(*parts)).read_text(encoding="utf-8")


def test_the_shipped_example_programme_verifies_clean(fired):
    """The example is the model's picture of a correct programme.

    If it carries so much as a warning, every programme written from it
    inherits the same flaw — and the model has no way to tell.
    """
    assert fired(SKILL.payload_dir / "references" / "examples" / "mini") == set()


def test_the_router_links_every_workflow_file():
    """A workflow the router cannot reach is a file nothing will ever read."""
    router = payload_text("SKILL.md")
    unreachable = [
        path.relative_to(SKILL.payload_dir).as_posix()
        for path in sorted((SKILL.payload_dir / "references" / "workflows").rglob("*.md"))
        if path.relative_to(SKILL.payload_dir).as_posix() not in router
    ]
    assert unreachable == []


def test_references_named_by_the_payload_all_exist():
    """A reference that points at a missing file fails silently: the model just
    carries on without the material it was told to read."""
    pattern = re.compile(r"`(references/[A-Za-z0-9_./-]+)`")
    missing = []
    for path in sorted(SKILL.payload_dir.rglob("*.md")):
        for match in pattern.finditer(path.read_text(encoding="utf-8")):
            if not (SKILL.payload_dir / match.group(1)).exists():
                missing.append(f"{path.relative_to(SKILL.payload_dir)} -> {match.group(1)}")
    assert missing == []


def test_the_router_names_the_real_cli_and_receipt():
    """The CLI-resolution block is how the model reaches the tool at all, and a
    stale name there is invisible: it silently falls through to "not installed"
    and asks the user to install a package that is not this one."""
    router = payload_text("SKILL.md")
    section = router[router.index("## Resolving the CLI") : router.index("## Step 1")]
    assert RECEIPT_NAME in section
    assert f"{CLI_NAME} --version" in section
    assert f"pip install {PACKAGE_NAME}" in section
    assert f"npm install -g {PACKAGE_NAME}" in section


def test_every_rule_id_appears_in_the_generated_reference():
    """`rules.md` is what the model reads when a finding names a rule."""
    text = payload_text("references", "rules.md")
    assert [rule.id for rule in rules.RULES if rule.id not in text] == []


def test_every_delivery_type_is_documented():
    text = payload_text("references", "schemas.md")
    assert [t for t in schedule.DELIVERY_TYPES if f"`{t}`" not in text] == []


def test_the_schedule_header_is_documented_verbatim():
    """The model writes this header by hand; a paraphrase in the docs produces
    a file that fails PRG-S01."""
    text = payload_text("references", "schemas.md")
    assert ",".join(schedule.SCHEDULE_HEADER) in text
