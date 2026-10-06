# Task — Plan the assessment

Agree what is being built before a single question or task is drafted: the
type, the level, the scope, the files, and where they go.

## Inputs

| Key | Required for | Default |
|---|---|---|
| `assessment_type` | all | infer from the request, then **confirm** |
| `format` | quiz, theory exam | `mcq` (a question CSV and an import file) or `oe` (written: brief, rubric, answer template); ask |
| `level` (+ `band`) | all | ask; see `references/assessment/levels.md` |
| `output_dir` | all | propose `.`, never assume silently |
| `subject_code` | all | ask |
| `seq` | all | auto (below), user may override |
| `scope_source` | all | ask: paste the scope, name a path to read, or point at an existing blueprint |
| `duration` | all | ask |
| `language` | all | English; a Vietnamese sibling only on request |
| `grade_pipeline` | assignments, exams | yes — controls the submission-archive naming |

A question set also needs its count, distributions, option count, time map and
delivery format; a capstone needs team size, sprint calendar, checkpoint gates,
stack and demo format. The workflow for the type lists its own.

## Produces

A confirmed plan, echoed back to the user. No files.

## Steps

1. Collect the inputs above, batched, asking only for what is missing.
2. Resolve `seq`: list `output_dir` **non-recursively**, match
   `^<subject>_<type_token>_(\d{2})`, take the highest plus one, or `01`. Name
   every file from `references/assessment/overview.md` § Naming.
3. Take the level's calibration: `FSA assessment levels show --level <LEVEL>
   [--band <BAND>] [--count N]`. Let the tool do the arithmetic.
4. For an exam, read what the module's labs and assignments drilled. The exam
   must be passable from that practice (see
   `references/assessment/tasks/design/write_brief.md` § The 80/20 rule) and
   must not reuse their domain.
5. Echo the plan: the absolute `output_dir`, every output filename, the level
   and its calibration, the task list or question distribution, any supplied
   files, and any Vietnamese siblings.

## Done when

The user has given an explicit go-ahead on the echoed plan.

## Hands off to

The authoring tasks the type's workflow lists.
