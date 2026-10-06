"""Payload-shape gates specific to the `assessment` skill.

Cross-skill invariants (payload validity against Codex's rules, no duplicate
names, version sync) live in the top-level `tests/test_consistency.py` instead
— these are the checks that only make sense for `assessment`'s own reference
graph: every assessment type has both a workflow and a verifier, and every
workflow file the router promises to route to actually exists.
"""

from __future__ import annotations

from get_fsa_training_done.skills.assessment import SKILL


def test_every_assessment_type_has_a_workflow_and_a_verifier():
    from get_fsa_training_done.skills.assessment.core.verify import ALL_TYPES

    payload = SKILL.payload_dir
    for assessment_type in ALL_TYPES:
        workflow = payload / "references" / "workflows" / "design" / f"{assessment_type}.md"
        verifier = payload / "references" / "verifiers" / f"{assessment_type}.md"
        assert workflow.is_file(), f"missing workflow for {assessment_type}"
        assert verifier.is_file(), f"missing verifier for {assessment_type}"


def test_the_router_links_every_workflow_file():
    payload = SKILL.payload_dir
    router = (payload / "SKILL.md").read_text(encoding="utf-8")
    for path in sorted((payload / "references" / "workflows").rglob("*.md")):
        relative = path.relative_to(payload).as_posix()
        assert relative in router, f"{relative} is not reachable from SKILL.md"


def test_references_named_by_workflows_all_exist():
    """A workflow that points at a missing reference fails silently — the model
    just carries on without the material it was told to read."""
    import re

    payload = SKILL.payload_dir
    pattern = re.compile(r"`(references/[A-Za-z0-9_./-]+)`")
    missing = []
    for path in sorted(payload.rglob("*.md")):
        for match in pattern.finditer(path.read_text(encoding="utf-8")):
            target = payload / match.group(1)
            if not target.exists():
                missing.append(f"{path.relative_to(payload)} -> {match.group(1)}")
    assert missing == []


def test_the_router_names_the_real_cli_and_receipt():
    """The CLI-resolution block is how the model reaches `FSA` at all.

    These names were `fsa-training-assessment` before the package was renamed, and a stale
    one is invisible: the model silently falls through to step 3 and asks the
    user to install a package that is not this one.
    """
    from get_fsa_training_done.__about__ import CLI_NAME, PACKAGE_NAME
    from get_fsa_training_done.install.receipt import RECEIPT_NAME

    router = (SKILL.payload_dir / "SKILL.md").read_text(encoding="utf-8")
    section = router[router.index("## Resolving the CLI") : router.index("## Step 1")]
    assert RECEIPT_NAME in section
    assert f"{CLI_NAME} --version" in section
    assert f"pip install {PACKAGE_NAME}" in section
    assert f"npm install -g {PACKAGE_NAME}" in section
