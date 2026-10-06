"""The rulebook for teaching material.

As in the programme skill: every finding names its rule, and
`references/structure.md` is generated from the same table the checker executes.

`MAT-D*` read one document. `MAT-C*` compare a module's materials against the
session plan that asks for them — the cross-skill half.
"""

from __future__ import annotations

from dataclasses import dataclass

from get_fsa_training_done.findings import ERROR, WARNING


@dataclass(frozen=True)
class Rule:
    id: str
    scope: str  # "document" | "coverage"
    severity: str
    title: str
    rationale: str


RULES: tuple[Rule, ...] = (
    Rule(
        "MAT-D01",
        "document",
        ERROR,
        "The filename follows the module's naming convention",
        "The index orders the module and reserves 00 for the handbook and 99 "
        "for the appendix. A file outside the pattern sorts unpredictably and "
        "is never linked from either.",
    ),
    Rule(
        "MAT-D02",
        "document",
        ERROR,
        "Indexes are unique within a folder",
        "Two notes claiming the same position give the module two orders.",
    ),
    Rule(
        "MAT-D03",
        "document",
        WARNING,
        "Indexes run without a gap",
        "A gap usually means a note was deleted or never written; advisory "
        "because a module may deliberately leave room.",
    ),
    Rule(
        "MAT-D04",
        "document",
        ERROR,
        "There is exactly one top-level heading, on the first line",
        "It is the document's title everywhere it is listed. A second one part "
        "way down reads as a new document to every renderer.",
    ),
    Rule(
        "MAT-D05",
        "document",
        ERROR,
        "There is no YAML front matter",
        "Nothing in this corpus carries any, and a renderer that does not "
        "expect it prints the block as content.",
    ),
    Rule(
        "MAT-D06",
        "document",
        ERROR,
        "The first section states what a learner will be able to do",
        "A note that opens with content has never said what it is for, and "
        "nothing downstream can map it to an objective.",
    ),
    Rule(
        "MAT-D07",
        "document",
        ERROR,
        "Numbered sections run 1..n without gaps or repeats",
        "The numbers are how a learner and an appendix refer to a part of the "
        "note; a repeat makes a reference ambiguous.",
    ),
    Rule(
        "MAT-D08",
        "document",
        ERROR,
        "The document ends with a knowledge check and somewhere to go next",
        "Without them a note stops rather than closing, and a learner has no "
        "way to test what they just read.",
    ),
    Rule(
        "MAT-D09",
        "document",
        WARNING,
        "The knowledge check asks enough questions",
        "A check with one or two questions samples a fraction of the note.",
    ),
    Rule(
        "MAT-D10",
        "document",
        ERROR,
        "Every fenced block declares a language",
        "An untagged fence loses highlighting, and the convention is what lets "
        "`text` mark the blocks that are diagrams rather than code.",
    ),
    Rule(
        "MAT-D11",
        "document",
        WARNING,
        "Fence languages come from the known set",
        "An unrecognised tag is usually a typo; advisory because a module may "
        "legitimately introduce a new language.",
    ),
    Rule(
        "MAT-D12",
        "document",
        ERROR,
        "Relative links resolve to a file that exists",
        "A note pointing at a sibling that was renamed or never written sends "
        "the reader nowhere, and nothing reports it at render time.",
    ),
    Rule(
        "MAT-D13",
        "document",
        ERROR,
        "Link anchors resolve to a heading in the target",
        "The appendix links into specific sections; a heading rename breaks them silently.",
    ),
    Rule(
        "MAT-D14",
        "document",
        ERROR,
        "A chapter ends with a link to what follows",
        "That footer is the module's reading order.",
    ),
    Rule(
        "MAT-D15",
        "document",
        ERROR,
        "A self-check list uses task-list items",
        "Learners tick them off; plain bullets cannot be ticked.",
    ),
    Rule(
        "MAT-D16",
        "document",
        WARNING,
        "English unless the filename marks a translation",
        "A translation is a separate artifact ending `_vn`, so the original "
        "stays the thing every other document links to.",
    ),
    Rule(
        "MAT-D17",
        "document",
        ERROR,
        "A lab guide has ordered steps and a checkable outcome",
        "A lab without steps is an assignment brief, and one without an "
        "acceptance list leaves a learner unable to tell when they are done.",
    ),
    Rule(
        "MAT-D18",
        "document",
        WARNING,
        "A lab guide declares its duration",
        "The session plan allots it a number of minutes; a lab that never "
        "states one cannot be checked against that.",
    ),
    Rule(
        "MAT-C01",
        "coverage",
        ERROR,
        "Every material the session plan names exists",
        "The plan is a promise about what will be taught. A named file that "
        "does not exist is a session with nothing to deliver.",
    ),
    Rule(
        "MAT-C02",
        "coverage",
        WARNING,
        "Every material in the folder is used by a session",
        "A note nobody schedules is either unfinished or forgotten.",
    ),
    Rule(
        "MAT-C03",
        "coverage",
        WARNING,
        "A material's objective codes match the session that uses it",
        "The plan says which objectives a session serves; material claiming "
        "different ones is teaching to a different goal.",
    ),
    Rule(
        "MAT-C04",
        "coverage",
        WARNING,
        "Every objective code cited is defined in the syllabus",
        "A code the syllabus does not list is a typo or a missing objective.",
    ),
)

BY_ID = {rule.id: rule for rule in RULES}

__all__ = ["BY_ID", "RULES", "Rule"]
