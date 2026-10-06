# Assessment — overview

Authors assessment artifacts, and grades submissions against them.

Read this before any assessment workflow or task: it holds the inputs to collect,
the commands, and the rules every assessment workflow assumes.

## Step 0 — Collect inputs

Ask only for what is missing. Batch the questions; do not interrogate one field
at a time.

**First, decide the intent** — is the user *designing* an assessment or
*grading* submissions? Infer it from the request, then confirm if ambiguous.

### Designing

| Key | Required for | Default |
|---|---|---|
| `assessment_type` | all | infer from the request, then **confirm** |
| `level` (+ `band`) | all | ask; see `references/assessment/levels.md` |
| `output_dir` | all | propose `.`, never assume silently |
| `subject_code` | all | ask |
| `seq` | all | auto (below), user may override |
| `scope_source` | all | ask: paste the scope, name a path to read, or point at an existing blueprint |
| `duration` | all | ask |
| `language` | all | English; ask only if the user hints at another |
| `grade_pipeline` | assignments, exams | yes — controls the submission-archive naming |

Question-set types also need question count, distributions, option count, time
map, and delivery formats; capstones need team size, the sprint calendar, the
sprint checkpoint gates, stack, and demo format. The workflow file for the type
lists its own.

### Grading

| Key | Default |
|---|---|
| `roster` | ask — a CSV with `ID`, `Name`, `Status` columns |
| `submissions_dir` | ask |
| `results_dir` | ask |
| `subject`, `submission_type` | ask |
| `brief_path`, `rubric_path` | ask (not needed for a quiz report) |
| comment language | English; ask only if the user hints at another |

Suggest a conventional path **only when it already exists** under a directory the
user named. Never invent one.

### A note on language

English is the default for everything the assessment feature emits, and any other language is
available on request — say so in the plan echo when one is used. Two things do
not follow the request:

- **Instructor rubrics stay English.** `verify` parses their section headings and
  `**Tn raw score**` rows, and the grading pipeline keys off them.
- **A capstone's sprint pack is generated, not written**, so it exists only in
  the languages `FSA assessment sprint-kit --lang` offers. If the user wants one that is not
  there, say so rather than hand-translating the output — a hand-edited pack is
  no longer derived from the spec, which is the whole reason it is generated.

### Then echo the plan

Before writing anything, report: the resolved **absolute** `output_dir` or
result paths, every output filename, the level and its calibration, and the
confirmed distribution. Wait for an explicit go-ahead.

## Naming

`stem = <subject_lower>_<type_token>_<seq>`

Resolve `seq` by listing `output_dir` **non-recursively** — it is the one
directory the user named — matching `^<subject>_<type_token>_(\d{2})`, taking the
highest plus one, or `01` when there is no match.

| `assessment_type` | `type_token` | Code abbrev | Archive token |
|---|---|---|---|
| `quiz` | `quiz` | `Q` | `quiz` |
| `short_assignment` | `short_assignment` | `SA` | `assignment` |
| `long_assignment` | `long_assignment` | `LA` | `assignment` |
| `theory_exam` | `theory_exam` | `TE` | `t_exam` |
| `practice_exam` | `practice_exam` | `PE` | `p_exam` |
| `capstone_project` | `capstone_project` | `PRJ` | `capstone` |

**The level never goes in the filename stem.** It appears in the display code and
a `Level:` banner line only. Putting it in the stem breaks rubric discovery and
the submission-archive contract in `references/assessment/grading_contract.md`.

So: file `jpl_short_assignment_02.md`, banner `Code: FR_JPL_SA_02` and
`Level: FR`, archive `jpl_assignment_02_<fpt_account>.zip`.

## Standing rules

- **Instructor-only files never reach learners.** Rubrics, master question CSVs,
  blueprints, and every cheat-check output. Only the brief, its PDF, and the
  platform import files are learner-facing.
- **Never execute learner code.** Grade from the submitted artifacts as evidence.
- **Import files are generated, never hand-written.** `FSA assessment emit` derives them
  from the master CSV so the two cannot drift. The same holds for a capstone's
  sprint pack: `FSA assessment sprint-kit` derives it from the project spec.
- **Report measurements, not impressions.** "4/4 A4 pages for a 2-hour exam" is a
  measurement; "about the right length" is not.

## Step 2 — Report back

List every file created with its full path, and say which of them are
learner-facing. For long-form work, give the task list with weights and the
rendered page count against the budget. For question
sets, give the confirmed structure and the actual-versus-target distribution.
Include the `FSA assessment verify` result and the verifier agent's verdict.

These are drafts for the user to review, not finished content to publish.
