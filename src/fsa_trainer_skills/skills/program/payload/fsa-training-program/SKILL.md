---
name: fsa-training-program
description: Design and verify FSA training programmes, and export the FPT vendor workbooks. Produces the training programme curriculum, master and detailed schedules, the outcome-standard to module mapping, the topic list, and one syllabus plus session-level schedule detail per topic. Use when asked to "thiết kế chương trình đào tạo", "viết syllabus", "lịch giảng dạy", "xuất file Excel", "design a training programme", "write a syllabus", "build the schedule", or "export the curriculum workbook".
---

# FSA training programme

Authors the structure of a training programme, checks that every artifact
reconciles against the others, and exports the vendor workbooks.

## What this skill does not own

It declares assessment **slots** — that a quiz exists, what it weighs, and the
filename that will serve it — and never the instrument itself.

| Artifact | Skill |
|---|---|
| questions, briefs, rubrics, import files, grading | `fsa-training-assessment` |
| lecture notes, handbooks, lab and demo guides | `fsa-training-material` |
| modules, schedules, syllabi, session plans, workbooks | this one |

A session's `Training Materials` cell names the file another skill produces.
When a finding is really about a missing instrument or a missing lecture note,
say so and name the skill that owns it rather than writing the file here.

## This skill is stateless

It knows nothing about the directory structure it was installed into and
assumes nothing about the project around it. **Every path it touches is one the
user gave it.**

> **Do not list, glob, read, or run anything until every required Step 0 value
> below has a confirmed value.** The only file you may read before that point is
> one the user has just named in this conversation.

The one path you legitimately know is `SKILL_DIR` — the directory containing the
`SKILL.md` you are reading right now.

## Step 0 — Collect inputs

Ask only for what is missing, and batch the questions.

| Key | Required for | Default |
|---|---|---|
| `program_dir` | all | ask; never assume |
| `program_code` | authoring | ask — the site, level, track and subject segments |
| `program_title`, `role` | authoring a curriculum | ask |
| `modules` | authoring a curriculum | ask: name, code, hours, days |
| `creator`, `account`, `unit` | authoring a syllabus | ask |
| `template_path` | export | ask; must be `.xlsx` |

**Never invent a programme constant.** The module count, the hour and day
totals, the minutes per training day, and the number of week and day columns are
all *derived* from the sources. If one cannot be derived, the sources disagree —
report that rather than picking a number.

Before writing anything, echo the resolved **absolute** paths, every output
filename, and the derived totals. Wait for an explicit go-ahead.

## Resolving the CLI

Do this once per session, before the first command, and call the result `FSA`.

1. Read `.fsa-trainer-skills-install.json` next to this `SKILL.md`; use its
   `cli.invocation` array, adding its `pythonpath` to `PYTHONPATH`.
2. Otherwise try `fsa-trainer-skills --version` on `PATH`.
3. Otherwise stop and ask the user to run `pip install fsa-trainer-skills` or
   `npm install -g fsa-trainer-skills`. Do not improvise a path to a script.

A receipt written on another machine names an interpreter that does not exist
here; when its invocation fails to run, fall through to option 2. If option 2
reports a version different from the `VERSION` file beside this `SKILL.md`, say
so — payload and CLI ship in lockstep.

`FSA` is the **bare CLI**, with no subcommand attached. This skill's own work
runs under its namespace — `FSA program verify` — while the lifecycle commands
every skill shares take no namespace: `FSA doctor`, `FSA status`, `FSA update`.
A worker verb written without its namespace resolves to nothing.

## Step 1 — Route to the workflow

Read **exactly one** workflow file — the one matching the confirmed intent. Do
not read the others.

| Intent | Workflow |
|---|---|
| author a programme and its schedules | `references/workflows/author/program.md` |
| author a topic's syllabus and session plan | `references/workflows/author/topic.md` |
| change a session plan and re-derive what follows | `references/workflows/author/revise.md` |
| read a verification report | `references/workflows/verify/report.md` |
| produce the vendor workbook | `references/workflows/export/workbooks.md` |

Supporting material, read as needed rather than up front:

| File | Holds |
|---|---|
| `references/artifact_map.md` | which file feeds which, and where the derived numbers come from |
| `references/schemas.md` | the exact CSV headers and the delivery-type vocabulary |
| `references/rules.md` | every verification rule, by id, with its rationale |
| `references/examples/mini/` | a small, complete, correct programme |

## Commands

| Command | Does |
|---|---|
| `FSA program verify --program-dir DIR` | reconcile every artifact; findings carry rule ids |
| `FSA program derive allocation --schedule CSV --syllabus MD --write` | recompute section 8 from the session plan |
| `FSA program derive skeleton --curriculum MD --out-dir DIR` | write the four CSV skeletons from the module table |
| `FSA program export syllabus --template T.xlsx --syllabus MD -o OUT` | fill the vendor workbook |

## Standing rules

- **Derived tables are never typed by hand.** The time-allocation shares come
  from the session plan, and the schedule column skeletons from the module
  table. Writing either by hand guarantees they drift.
- **Report measurements, not impressions.** "1200 of 1200 minutes across 5 days"
  is a measurement; "about right" is not.
- **The vendor template is the customer's property.** Ask for its path; never
  copy one into a repository, and never ship one with a programme.
- **Assessment instruments and teaching materials belong to the sibling skills.**
  A session row names the file that serves it; producing that file is
  `fsa-training-assessment`'s or `fsa-training-material`'s job, not this one's.

## Step 2 — Report back

List every file written with its full path, the derived totals, and the
`FSA program verify` result with its rule ids.
