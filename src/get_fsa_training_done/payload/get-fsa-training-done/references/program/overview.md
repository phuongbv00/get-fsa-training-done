# Programme — overview

Authors the structure of a training programme, checks that every artifact
reconciles against the others, and exports the vendor workbooks.

Read this before any program workflow or task: it holds the inputs to collect,
the commands, and the rules every program workflow assumes.

## What this feature does not own

It declares assessment **slots** — that a quiz exists, what it weighs, and the
filename that will serve it — and never the instrument itself.

| Artifact | Feature |
|---|---|
| questions, briefs, rubrics, import files, grading | the assessment feature |
| lecture notes, handbooks, lab and demo guides | the material feature |
| modules, schedules, syllabi, session plans, workbooks | this one |

A session's `Training Materials` cell names the file another feature produces.
When a finding is really about a missing instrument or a missing lecture note,
say so and name the feature that owns it rather than writing the file here.

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
- **Assessment instruments and teaching materials belong to the other features.**
  A session row names the file that serves it; producing that file is
  the assessment feature's or the material feature's job, not this one's.

## Step 2 — Report back

List every file written with its full path, the derived totals, and the
`FSA program verify` result with its rule ids.
