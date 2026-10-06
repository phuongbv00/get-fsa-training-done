# Assessment — overview

Authors assessment artifacts, and grades submissions against them. Read this
before any assessment workflow or task: it holds the naming, the language rule
and the standing rules every one of them assumes. Each task lists its own
inputs.

## Naming

`stem = <subject_lower>_<type_token>_<seq>`

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

Files that go with a stem are named `<stem>_<role>`: `_rubric.md`,
`_answer_template.md`, `_template.md`, `_seed.sql`, `_starter.zip`,
`_repo.zip`, `_blooket.csv`, `_coderbyte.json`. A Vietnamese sibling follows
`references/common/language_vn.md`.

## Language

English is the default for everything this feature emits; Vietnamese is a
`_vn` sibling on request, written by `references/common/tasks/translate_vn.md`.
Two things never follow the request:

- **Instructor rubrics stay English.** `verify` parses their section headings and
  `**Tn raw score**` rows, and the grading pipeline keys off them.
- **A capstone's sprint pack is generated, not written**, so it exists only in
  the languages `FSA assessment sprint-kit --lang` offers. Say so rather than
  hand-translating it.

Everything written follows `references/common/style.md`.

## Standing rules

- **Instructor-only files never reach learners.** Rubrics, master question CSVs,
  reference schemas, seed tests, blueprints, and every cheat-check output.
  Learner-facing: the brief and its PDF, answer templates and worksheets,
  supplied files. Import files go to the platform only.
- **Never run learner code on this machine.** Grade from the submitted files as
  evidence; anything that must run, runs through `FSA assessment sandbox`
  (`references/common/tasks/run_in_sandbox.md`).
- **Supplied files are proven before they are handed out.** A seed that fails to
  load or a mock API that answers wrongly is a defect in the exam.
- **Import files are generated, never hand-written.** `FSA assessment emit`
  derives them from the master CSV, and `FSA assessment sprint-kit` derives a
  capstone's sprint pack from its spec.
- **Report measurements, not impressions.** "4/4 A4 pages for a 2-hour exam" is a
  measurement; "about the right length" is not.

## Report back

List every file created with its full path and say which are learner-facing.
For long-form work, give the task list with weights and the page count against
the budget; for question sets, the confirmed structure and the actual-versus-
target distribution; for supplied files, their sandbox results. Include the
`FSA assessment verify` result and the verifier agent's verdict.

These are drafts for the user to review, not finished content to publish.
