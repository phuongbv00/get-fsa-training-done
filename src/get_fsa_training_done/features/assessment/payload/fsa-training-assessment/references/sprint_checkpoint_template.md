# Sprint checkpoint template

A capstone is graded once, at the defence. Everything the rubric wants to say
about *how the team worked* — that the backlog guided the work, that code
landed steadily, that one member did not carry four — has to be evidence that
already exists by then, with a date on it. Evidence like that is not produced
retroactively. It is produced at a checkpoint, or not at all.

So each sprint ends with the same four gates plus whatever that sprint owns.
The gates are a **checklist** the team reads, and a **form** the instructor
fills. They are the same five rows seen from two sides, so this file covers
both: how the checklist is generated, and what the form contains.

Both are English by default. The checklist is generated, so it exists in the
languages `FSA assessment sprint-kit --lang` offers; the form below is instructor-only and
stays English.

---

## The five gates

| Gate | What it is | Why it is a gate and not a nice-to-have |
|---|---|---|
| G1 | Backlog freeze | A backlog that changes silently cannot show who committed to what |
| G2 | Code tag | An annotated git tag is the only timestamp a team cannot backdate by hand |
| G3 | Submission folder | Fixed layout, or grading turns into a scavenger hunt across ten Drives |
| G4 | Sprint review record | The primary dated evidence of individual contribution |
| G5 | Sprint deliverable | The artifact that sprint's row in the spec's table says is due |

G1–G4 are identical every sprint. G5 is the only one that changes, and its
content comes from the spec, never from here.

---

## 1. The checklist — generated, never hand-written

```bash
FSA assessment sprint-kit --spec "<output_dir>/<stem>_spec.md" --drive-root "<CLASS>" --update-spec
```

Reads the spec's `## Sprints` table and writes, next to the spec:

| File | Goes to | What it is |
|---|---|---|
| `SUBMISSION_GUIDE.md` | the teams | Sprint calendar with real deadlines, the five gates, and a tick-box checklist per sprint |
| `backlog_template.csv` | the teams | The G1 column header, with two filled example rows |
| `sprint_review_template.md` | the teams | The G4 skeleton |
| `spec_sprint_checkpoint.md` | the spec | The `## Sprint checkpoint` section; `--update-spec` writes it in for you |

Hand the first three to the teams. The fourth is the same text seen from the
spec's side, which is the point: the gate wording lives in exactly one place in
the codebase, so the handout a team reads, the section `verify` checks, and the
caps the rubric applies cannot disagree about what G2 means.

The command refuses to run against a sprint calendar that fails verification —
a handout with a deadline the spec does not have is worse than no handout.

**`--drive-root` is not optional in practice.** Without it the handout says
`<CLASS>/<TEAM>/Sprint 1/`, which is not a folder anybody can find; the command
warns when you leave it out.

**`--lang` defaults to `en`.** Pass the language the brief and spec use, so the
checkpoint section the spec carries and the handout a team reads are the same
document. Gate ids stay `G1`–`G5` in every language, which is what lets `verify`
and the rubric's caps work unchanged.

To change gate wording, or to add a language, edit `core/sprintkit.py` and
regenerate. Editing the generated files — including translating one by hand — is
how the drift this whole design prevents gets reintroduced.

## 2. The form — instructor-only, one per team per sprint

Filled during the sprint review, not at the defence. The sub-criteria sum to
10.0, the same raw scale every rubric task uses, so the sprint scores average
straight into the sprint-process task without conversion.

```markdown
# Sprint <N> Checkpoint — <TEAM>

> **Reviewed:** <YYYY-MM-DD> by <instructor>

| Criterion | Points | Full mark |
|---|---|---|
| Backlog integrity (G1) | 2.5 | Both snapshots present; every task has one assignee and an estimate; closing statuses reconcile with what is in the tag; every post-freeze task carries its `Added` date |
| Delivery on the tag (G2) | 2.5 | `sprint-<N>` is an annotated tag on the default branch, pushed before the deadline, and the tree at that tag contains the stories marked Done |
| Submission completeness (G3) | 1.5 | Every file in the G3 table is in `<CLASS>/<TEAM>/Sprint <N>/`, named exactly, uploaded before the deadline |
| Review record (G4) | 1.5 | Done / not-done reconciles with the closing backlog; scope changes explained; per-member lines name task ids, not attitudes |
| Sprint deliverable (G5) | 2.0 | The artifact this sprint owns is present and reviewable. **Its content is scored in T1–T5, not here** |
| **Sprint <N> raw score** | **10.0** | |

## Gates missed

<List gate ids, or "none". This list is what the final rubric's caps read.>

## Notes for the final grade

<One or two lines an instructor at the defence needs and would not otherwise
have: who was absent, what the team was told, what they were let off.>
```

**G5 is scored on delivery, not on quality.** The requirement-and-design
document is worth 15% of the capstone in T3, and it is graded there once, in
full. Grading it again here would mean a team that wrote a weak document loses
points twice for one artifact — exactly the double-counting the capstone
verifier looks for.

---

## 3. Where the scores land

One task in the rubric, sitting alongside the deliverable tasks:

| Task | Deliverable | Suggested weight |
|---|---|---|
| T1 | D01 Project Proposal | 10% |
| T2 | D02 Product Backlog and WBS | 10% |
| T3 | D03 Requirement and Design Documents | 15% |
| T4 | D04 Source Code | 30% |
| T5 | D05 Final Presentation and Demo | 10% |
| T6 | Sprint Process | 10% |
| T7 | Individual Contribution | 15% |

`T6 raw score = mean of the sprint raw scores, to one decimal place.`

T2 and T6 look adjacent and are not. **T2 grades the backlog as an artifact** —
whether the stories are decomposed sensibly, whether the WBS is complete.
**T6 grades whether the process happened on the dates it claimed to.** A team
can write an excellent backlog the night before the defence: full marks on T2,
zero on T6, and both are correct.

---

## 4. Caps — goes in the rubric, under `## 4. Caps and Deductions`

Gates cost something or they are not gates. That section is grouped one
subsection per task, and each entry below is an absolute maximum for **that
task's raw 0-10 score**, never for the final total — the lowest applicable cap
for a task wins and caps are never additive. See
`references/grading_contract.md` §3.

### T2 - D02 Product Backlog and WBS

| Trigger | Effect |
|---|---|
| G1 missed in half the sprints or more | cap 5.0 — a backlog that was never frozen did not guide the work |

### T4 - D04 Source Code

| Trigger | Effect |
|---|---|
| G3 missed | the sprint deliverable is graded from whatever the folder held at the deadline; nothing uploaded later is read |

### T6 - Sprint Process

| Trigger | Effect |
|---|---|
| Any gate missed in a sprint | that sprint's checkpoint raw score capped at 5.0 |
| G2 missing or tagged after the deadline in any sprint | cap 6.0; the code itself is still graded on its merits in T4 |
| G5 missed | that sprint's G5 criterion scores 0, and the deliverable's own task carries the standard late treatment |

### T7 - Individual Contribution

| Trigger | Effect |
|---|---|
| G4 missing in any sprint | cap 7.0 for every member of that team — the record is the primary dated evidence of who did what |

Write the caps with the gate ids in them. `FSA assessment verify --type capstone_project`
reads this section looking for `G1`–`G5`, and warns for every gate that appears
in the checkpoint but has no consequence here.

---

## Fitting a different number of sprints

Nothing above assumes three. G1–G4 repeat for however many rows the spec's
`## Sprints` table has, and G5 reads its content from that row. Two constraints:

- **Every one of D01–D05 is due in exactly one sprint.** The verifier enforces
  this. A deliverable in no sprint can never be late; one in two sprints has
  two deadlines.
- **A single-sprint capstone has no sprint process to score.** Drop T6 and
  reweight; the verifier only requires the task when the spec runs two or more.
