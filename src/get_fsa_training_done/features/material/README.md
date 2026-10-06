# `material` — writing and checking teaching material

Write the teaching material a session plan calls for, and check that what the
plan promises exists. The agent writes the content; the CLI checks the shape
everything downstream depends on and derives the one part that must not be
maintained by hand.

| | |
| --- | --- |
| Namespace | `material` |
| Part of the skill | `get-fsa-training-done` |
| Worker commands | `get-fsa-training-done material <verb>` |
| Payload | [`references/material/`](../payload/get-fsa-training-done/references/material) |

## Artifacts

| Artifact | File |
| --- | --- |
| Lecture note | `NN_Topic_Name.md` |
| Module handbook | `00_Study_Guide_Handbook.md` — index `00` is reserved |
| Module appendix | `99_Appendix.md` — index `99` is reserved; its syllabus map is derived |
| Lab guide | `<subject>_lab_NN.md` |
| Group worksheet | `<subject>_lab_NN_worksheet.md` — a blank form beside a group lab |

A lab guide is the **guided middle**: shorter than an assignment,
step-numbered, and checkable by the learner without a marker. If it carries
marks and a rubric it is an assignment, and it belongs to the assessment
feature.

Material is written to the trainee, never as trainer notes. Diagrams are
`mermaid`; ER relationships state their cardinality in words (`MAT-D19`) and
colours come from the theme (`MAT-D20`), so a diagram reads in light and dark
mode alike.

## The seam with the other two features

A session row in a programme's plan names the file that serves it. That column
is the contract:

```csv
1,Semantic HTML,1,"Lab: build an accessible two-breakpoint page",FEF-K1,Assignment/Lab,90,Blended,fef_lab_01.md
1,Relational Modelling,1,Quiz 1 — modelling scenarios (MCQ),DBF-K1,Test/Quiz,30,Blended,dbf_quiz_01.csv
```

The program feature writes the row. This feature produces `fef_lab_01.md`; the
assessment feature produces `dbf_quiz_01.csv`. `coverage` reports what is
missing on this side and counts the rest as *owned by another skill* rather than
as a gap — reporting a missing quiz here would send someone to write the wrong
thing.

## Worker commands

### `verify` — is the document well formed?

```bash
get-fsa-training-done material verify "training_program/10. RE/Lectures"
get-fsa-training-done material verify dbf_lab_01.md --type lab
```

Structural only: whether a note *teaches* well is the model's judgement. What
this checks is what everything downstream depends on — one title on line 1, no
front matter, an objectives section that says what a learner will be able to do,
contiguous section numbers, a language tag on every fence, and every link and
`#anchor` resolving.

Prefer a folder: the index rules (unique, contiguous, `00`/`99` reserved) only
mean anything across a whole module.

22 rules, `MAT-D*` for one document and `MAT-C*` against the session plan. Every
finding names its rule, and
[`references/material/structure.md`](../payload/get-fsa-training-done/references/material/structure.md)
is **generated** from `core/grammar.py` and `core/rules.py` — prose describing a
required section the checker does not enforce would calibrate the model to a
constraint nothing holds it to.

### `coverage` — does what the plan asks for exist?

```bash
get-fsa-training-done material coverage \
  --schedule HN_FR_JSKS_FEF_ScheduleDetail.csv \
  --dir "training_program/5. FEF/Lectures" \
  --syllabus HN_FR_JSKS_FEF_Syllabus.md
```

Both directions: a file the plan names that does not exist is an error, a file
present that no session uses is a warning. With `--syllabus` it also checks the
objective codes against the syllabus, and that a material mentions the
objectives its session claims.

It reads the plan **by column name, tolerating any superset**, and deliberately
does not enforce that CSV's schema — that is `program verify`'s job. Each skill
checks only what it owns, so there is no shared constant to drift.

### `derive appendix` — the syllabus map

```bash
get-fsa-training-done material derive appendix \
  --syllabus TOPIC_Syllabus.md --dir ./Lectures --appendix 99_Appendix.md --write
```

Matches each topic-outline item to the note whose headings best cover it and
writes `- [ ] <item> → [NN](NN_File.md#anchor)`. Those anchors are the only deep
links in a module, so a renamed heading breaks them and nothing else reports it
— which is the case for deriving the map rather than maintaining it. It is a
match on wording, so the result is meant to be read: an item linked to the wrong
note says the outline and the notes use different words for the same thing.

`--check` is the drift gate; `--write` is idempotent.

## Templates

The corpus this generalises holds three generations of lecture note. The skill
standardises on the newest — the **unit** template, used by the three most
recently authored modules — and recognises the older **chapter** form so those
files can be checked rather than rewritten.

Expect existing material to report findings. The two oldest notes in the corpus
have a mid-file `#` heading, untagged fences and no knowledge check; that is a
true description of them, not a false alarm.

## Language

English by default. A translation is a **separate file** whose stem ends `_vn`,
never a rewrite of the original — everything else links to the original, so
replacing it in place breaks those links and leaves half a module in one
language. `verify` warns about Vietnamese in a file not marked that way.

## Prerequisites

None.

## Layout

```
features/material/
├── commands/            # verify, coverage, derive
└── core/
    ├── grammar.py       # the templates — source for structure.md
    ├── rules.py         # the rulebook — same
    ├── notes.py         # headings, fences, links
    ├── checks.py        # MAT-D* rule bodies
    ├── coverage.py      # MAT-C*, the cross-feature half
    └── appendix.py      # the derived syllabus map

payload/get-fsa-training-done/references/material/
├── overview.md
├── structure.md         # GENERATED
├── conventions.md
├── templates/
├── examples/{mini,plan}/
├── tasks/
└── workflows/
```

## Development

```bash
python scripts/material/gen_structure_md.py       # after editing grammar.py or rules.py
```

CI runs it with `--check`.

The clean example module lives in the payload
([`references/material/examples/mini/`](../payload/get-fsa-training-done/references/material/examples/mini)),
with the session plan that asks for it in `examples/plan/`. Consistency gates
assert it verifies clean *and* covers its plan exactly, and that every shipped
template would itself pass the checker — a skeleton the checker rejects teaches
the wrong shape. Failing cases are copies of the example with one targeted edit.
