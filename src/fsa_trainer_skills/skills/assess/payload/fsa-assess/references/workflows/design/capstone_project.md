# Workflow — capstone project

Team work over several weeks, ending in a defence. The largest thing this skill
produces, and the only one where the assessment unit is a group.

**Produces:** `<stem>.md`, `<stem>_spec.md`, `<stem>_rubric.md`, `<stem>.pdf`

**Language: Vietnamese** for the brief and spec, matching the existing project
material. The rubric stays English, like every other rubric.

## 1. Collect the extra inputs

Beyond Step 0, a capstone needs decisions that nothing else does:

| Input | Notes |
|---|---|
| team size | how many, and how teams are formed |
| duration | total, plus the defence date |
| sprints | how many, how long, what is due at the end of each |
| stack | what is mandated, what is free choice |
| demo format | length, structure, per-member speaking requirement |
| contribution | how individual contribution is measured |

These are exactly the things that get referred to and never defined. Get them
before drafting.

## 2. Write the topic brief — `<stem>.md`

```markdown
# Capstone Project - <Tên dự án>

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

- **Mô tả core** — what the system must do at minimum;
- **Bonus AI** — an optional AI-flavoured extension;
- **Bonus tích hợp 3rd-party** — an optional integration.

Keep bonuses genuinely optional and say so in the weighting, or they become
mandatory work nobody planned for.

### Tasks are the five deliverables

Map them one to one, plus an individual-contribution task:

| Task | Deliverable |
|---|---|
| T1 | D01 Project Proposal |
| T2 | D02 Product Backlog and WBS |
| T3 | D03 Requirement and Design Documents |
| T4 | D04 Source Code |
| T5 | D05 Final Presentation and Demo |
| T6 | Individual contribution |

Weights sum to 100%. Source code should carry the largest share; the individual
contribution needs enough weight to matter — around 15% is a reasonable start.

Diagrams are **diagram-as-code** (`.drawio`, Mermaid, dbdiagram.io, PlantUML).
Exported images are not accepted, and that belongs in the deliverable bullet.

## 3. Write the spec — `<stem>_spec.md`

Copy the structure from `references/capstone_spec_template.md` and fill in every
section from the inputs collected in step 1. All six are required, and the
verifier checks for them.

## 4. Write the rubric — `<stem>_rubric.md`

The standard six sections, so the grading pipeline consumes it unchanged. The
task list is T1–T6 above, with ids and weights matching the brief exactly.

Two things specific to a capstone:

**Team versus individual.** T1–T5 score the team's artifacts; T6 scores the
person. Say in T6's full-mark evidence what counts — commit history, sprint
minutes, the part they presented — so two graders reach the same number.

**Process is evidence, not decoration.** A backlog that was written the night
before the defence is not a backlog. Where a criterion is about process, make
the evidence something with a timestamp.

## 5. Render and verify

```bash
FSA render "<output_dir>/<stem>.md"
FSA verify --type capstone_project \
  --brief  "<output_dir>/<stem>.md" \
  --spec   "<output_dir>/<stem>_spec.md" \
  --rubric "<output_dir>/<stem>_rubric.md" \
  --pdf    "<output_dir>/<stem>.pdf" \
  --level  "<LEVEL>"
```

There is no page budget — the duration is measured in weeks — but the render
still produces the PDF that gets handed out.

## 6. Verifier agent

Run `references/verifiers/capstone_project.md`.
