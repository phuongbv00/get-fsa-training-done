# Workflow — capstone project

Team work over several weeks, ending in a defence. The largest thing this skill
produces, and the only one where the assessment unit is a group.

**Produces:** `<stem>.md`, `<stem>_spec.md`, `<stem>_rubric.md`, `<stem>.pdf`,
and `<stem>_sprint_kit/` — the pack the teams receive

**Language: English by default**, like every other type, and another language
on request. The rubric always stays English — `verify` and the grading pipeline
parse it. Whatever the brief and spec use, pass the same `--lang` to the step 5
generator so a team reads the wording the rubric grades against.

## 1. Collect the extra inputs

Beyond Step 0, a capstone needs decisions that nothing else does:

| Input | Notes |
|---|---|
| team size | how many, and how teams are formed |
| duration | total, plus the defence date |
| sprints | how many, the start and end date of each, and which deliverables each one is due |
| checkpoint | the sprint gates, and what missing one costs — `references/sprint_checkpoint_template.md` |
| drive root | the Drive folder the team folders sit under, e.g. `MKP-F26` |
| stack | what is mandated, what is free choice |
| demo format | length, structure, per-member speaking requirement |
| contribution | how individual contribution is measured |

These are exactly the things that get referred to and never defined. Get them
before drafting.

## 2. Write the topic brief — `<stem>.md`

```markdown
# Capstone Project - <Project name>

> **Code:** <LEVEL>_<SUBJ>_PRJ_<seq>
> **Level:** <LEVEL>
> **Duration:** <duration>
> **Topics:** <topic> | <topic>

---

## 1. Problem Statement
## 2. Tasks
## 3. Deliverables
```

The three-section shape holds. Within it, a capstone topic is usually described
in three parts, following the existing project material:

- **Core scope** — what the system must do at minimum;
- **Bonus AI** — an optional AI-flavoured extension;
- **Bonus third-party integration** — an optional integration.

Keep bonuses genuinely optional and say so in the weighting, or they become
mandatory work nobody planned for.

### Tasks are the five deliverables

Map them one to one, then add the two tasks nothing else in the skill has —
one for the sprint process, one for the individual:

| Task | Deliverable | Suggested weight |
|---|---|---|
| T1 | D01 Project Proposal | 10% |
| T2 | D02 Product Backlog and WBS | 10% |
| T3 | D03 Requirement and Design Documents | 15% |
| T4 | D04 Source Code | 30% |
| T5 | D05 Final Presentation and Demo | 10% |
| T6 | Sprint Process | 10% |
| T7 | Individual contribution | 15% |

Weights sum to 100%. Source code carries the largest share; the individual
contribution needs enough weight to matter. T6 aggregates the sprint checkpoint
scores and only exists when the spec runs two or more sprints — a single-sprint
capstone drops it and reweights.

Diagrams are **diagram-as-code** (`.drawio`, Mermaid, dbdiagram.io, PlantUML).
Exported images are not accepted, and that belongs in the deliverable bullet.

## 3. Write the spec — `<stem>_spec.md`

Copy the structure from `references/capstone_spec_template.md` and fill in every
section from the inputs collected in step 1. All seven are required, and the
verifier checks for them.

Two of them are parsed rather than read, so their shape is not a matter of taste:

- **`## Sprints`** is a table — number, ISO start, ISO end, deliverables due.
  Each of D01–D05 lands in exactly one sprint, and every `Sprint N` the brief
  mentions has to be a row here.
- **`## Sprint checkpoint`** names gates `G1`–`G5`. **Write the heading and
  nothing else** — step 5 generates the body with `FSA assessment sprint-kit --update-spec`
  from the same source the learner handout comes from.

## 4. Write the rubric — `<stem>_rubric.md`

The standard six sections, so the grading pipeline consumes it unchanged. The
task list is T1–T7 above, with ids and weights matching the brief exactly.

Three things specific to a capstone:

**Team versus individual.** T1–T6 score the team; T7 scores the person. Say in
T7's full-mark evidence what counts — commit history, the per-member lines in
the sprint review records, the part they presented — so two graders reach the
same number.

**Process is evidence, not decoration.** A backlog that was written the night
before the defence is not a backlog. Where a criterion is about process, make
the evidence something with a timestamp.

**The gates need caps.** Section 4 states what each of `G1`–`G5` costs when it
is missed; the table in `references/sprint_checkpoint_template.md` §4 is the
default set. `FSA assessment verify` reads that section for gate ids and warns for any gate
the checkpoint defines but nothing penalises. T6 is scored from the per-sprint
checkpoint forms — its raw score is their mean — so say that in T6's scoring
guide rather than inventing a second scale.

## 5. Generate the sprint pack — `<stem>_sprint_kit/`

The teams need the calendar, the gates, and the templates they fill. All of it
is derived from the spec, never written by hand:

```bash
FSA assessment sprint-kit --spec "<output_dir>/<stem>_spec.md" \
  --drive-root "<CLASS>" --lang "<en|vi>" --update-spec
```

`--lang` matches the confirmed `language`; it defaults to `en`. The pack is
generated rather than translated, so only the languages the command lists exist.
If the user asks for one that is not there, say so — do not hand-translate the
output, which would stop it being derived from the spec.

`--drive-root` is the Drive folder the team folders sit under, e.g. `MKP-F26`.
Ask for it in step 1 if it did not come up; without it the handout points at
`<CLASS>/<TEAM>/…`, which is not a folder anybody can open.

`--update-spec` writes the generated `## Sprint checkpoint` section into the
spec, so add the bare heading in step 3 and let the command fill it. That is
what keeps the gate wording identical in the handout, the spec, and the caps.

Three of the four files go to the teams — `SUBMISSION_GUIDE.md`,
`backlog_template.csv`, `sprint_review_template.md`. `spec_sprint_checkpoint.md`
is the spec's copy and does not need handing out. Details in
`references/sprint_checkpoint_template.md`.

The per-sprint instructor form is **not** generated: it is instructor-only, and
generating it beside three learner-facing files is how it ends up in the same
Drive folder. Copy it from `references/sprint_checkpoint_template.md` §2.

## 6. Render and verify

```bash
FSA assessment render "<output_dir>/<stem>.md"
FSA assessment verify --type capstone_project \
  --brief  "<output_dir>/<stem>.md" \
  --spec   "<output_dir>/<stem>_spec.md" \
  --rubric "<output_dir>/<stem>_rubric.md" \
  --pdf    "<output_dir>/<stem>.pdf" \
  --level  "<LEVEL>"
```

`--level` takes the band with it for the banded levels — `UP_SKILL:mid`,
`RE_SKILL:senior` — and the level alone for `CPL` and `FR`.

There is no page budget — the duration is measured in weeks — but the render
still produces the PDF that gets handed out.

## 7. Verifier agent

Run `references/verifiers/capstone_project.md`.
