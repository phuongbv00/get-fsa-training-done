"""Payload-shape gates specific to the `assessment` feature.

Payload-wide invariants (the router reaches every workflow, every named
reference exists, the CLI block is current) live in the top-level
`tests/test_consistency.py`. This is the check that only makes sense for
`assessment`: every assessment type has both a workflow and a verifier.
"""

from __future__ import annotations

from get_fsa_training_done.skill import SKILL

FEATURE = SKILL.payload_dir / "references" / "assessment"


def test_every_assessment_type_has_a_workflow_and_a_verifier():
    from get_fsa_training_done.features.assessment.core.verify import ALL_TYPES

    for assessment_type in ALL_TYPES:
        workflow = FEATURE / "workflows" / "design" / f"{assessment_type}.md"
        verifier = FEATURE / "verifiers" / f"{assessment_type}.md"
        assert workflow.is_file(), f"missing workflow for {assessment_type}"
        assert verifier.is_file(), f"missing verifier for {assessment_type}"
