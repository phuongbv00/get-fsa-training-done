---
name: fsa-assess
description: Design and grade FSA training assessments. Design produces quizzes, short and long assignments, theory exams, practice exams, and capstone projects — as learner briefs, instructor rubrics, master question CSVs, and platform import files. Grading preprocesses submissions, scores them against a rubric, aggregates results, scores quiz reports, and runs instructor-only copying and AI-authorship checks. Use when asked to "tạo assignment", "ra đề", "thiết kế bài tập", "tạo quiz", "tạo theory exam", "tạo đồ án", "design an assessment", "chấm điểm", "chấm bài", "grade submissions", or "aggregate grades".
---

# FSA assessment

Authors assessment artifacts, and grades submissions against them.

## This skill is stateless

It knows nothing about the directory structure it was installed into and
assumes nothing about the project around it. **Every path it touches is one the
user gave it.**

> **Do not list, glob, read, or run anything until every required Step 0 value
> below has a confirmed value.** The only file you may read before that point is
> one the user has just named in this conversation. Do not infer values from the
> working directory, from folder names, or from files you happen to notice.

The one path you legitimately know is `SKILL_DIR` — the directory containing the
`SKILL.md` you are reading right now. Reference files below are relative to it.

## Step 0 — Collect inputs

Ask only for what is missing. Batch the questions; do not interrogate one field
at a time.

**First, decide the intent** — is the user *designing* an assessment or
*grading* submissions? Infer it from the request, then confirm if ambiguous.

### Designing

| Key | Required for | Default |
|---|---|---|
| `assessment_type` | all | infer from the request, then **confirm** |
| `level` (+ `band`) | all | ask; see `references/levels.md` |
| `output_dir` | all | propose `.`, never assume silently |
| `subject_code` | all | ask |
| `seq` | all | auto (below), user may override |
| `scope_source` | all | ask: paste the scope, name a path to read, or point at an existing blueprint |
| `duration` | all | ask |
| `language` | all | English, except `capstone_project` which is Vietnamese |
| `grade_pipeline` | assignments, exams | yes — controls the submission-archive naming |

Question-set types also need question count, distributions, option count, time
map, and delivery formats; capstones need team size, sprints, stack, and demo
format. The workflow file for the type lists its own.

### Grading

| Key | Default |
|---|---|
| `roster` | ask — a CSV with `ID`, `Name`, `Status` columns |
| `submissions_dir` | ask |
| `results_dir` | ask |
| `subject`, `submission_type` | ask |
| `brief_path`, `rubric_path` | ask (not needed for a quiz report) |
| comment language | Vietnamese |

Suggest a conventional path **only when it already exists** under a directory the
user named. Never invent one.

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
the submission-archive contract in `references/grading_contract.md`.

So: file `jpl_short_assignment_02.md`, banner `Code: FR_JPL_SA_02` and
`Level: FR`, archive `PhuongBV3_jpl_assignment_02.zip`.

## Resolving the CLI

Do this once per session, before the first command, and call the result `FSA`.

1. Read `.fsa-assess-install.json` next to this `SKILL.md`; use its
   `cli.invocation` array, adding its `pythonpath` to `PYTHONPATH`.
2. Otherwise try `fsa-assess --version` on `PATH`.
3. Otherwise stop and ask the user to run `pip install fsa-assess` or
   `npm install -g fsa-assess`. Do not improvise a path to a script.

If option 2 works but reports a version different from the `VERSION` file beside
this `SKILL.md`, prefer option 1 — payload and CLI ship in lockstep, and an older
CLI left on `PATH` is not the one these workflows were written against.

## Routing

Read **exactly one** workflow file — the one matching the confirmed type. Do not
read the others.

| Intent | Type | Workflow | Verifier prompt |
|---|---|---|---|
| design | `quiz` | `references/workflows/design/quiz.md` | `references/verifiers/quiz.md` |
| design | `short_assignment` | `references/workflows/design/short_assignment.md` | `references/verifiers/short_assignment.md` |
| design | `long_assignment` | `references/workflows/design/long_assignment.md` | `references/verifiers/long_assignment.md` |
| design | `theory_exam` | `references/workflows/design/theory_exam.md` | `references/verifiers/theory_exam.md` |
| design | `practice_exam` | `references/workflows/design/practice_exam.md` | `references/verifiers/practice_exam.md` |
| design | `capstone_project` | `references/workflows/design/capstone_project.md` | `references/verifiers/capstone_project.md` |
| grade | assignments and exams | `references/workflows/grade/submissions.md` | — |
| grade | quiz report | `references/workflows/grade/quiz_report.md` | — |
| grade | copying / AI authorship | `references/workflows/grade/cheat_check.md` | — |

## Standing rules

- **Instructor-only files never reach learners.** Rubrics, master question CSVs,
  blueprints, and every cheat-check output. Only the brief, its PDF, and the
  platform import files are learner-facing.
- **Never execute learner code.** Grade from the submitted artifacts as evidence.
- **Import files are generated, never hand-written.** `FSA emit` derives them
  from the master CSV so the two cannot drift.
- **Report measurements, not impressions.** "4/4 A4 pages for a 2-hour exam" is a
  measurement; "about the right length" is not.

## Step 2 — Report back

List every file created with its full path. For long-form work, give the task
list with weights and the rendered page count against the budget. For question
sets, give the confirmed structure and the actual-versus-target distribution.
Include the `FSA verify` result and the verifier agent's verdict.

These are drafts for the user to review, not finished content to publish.
