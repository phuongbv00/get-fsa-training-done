# Workflow — quiz scores

A module's quiz results, from wherever they came, to scores out of 10 and the
workbook FAMS imports — not the assignment pipeline: no preprocessing, no
batches, no score sheets. Run it once per module (JCF, SBAD…), over all of that
module's quizzes at once.

| Step | Task | Notes |
|---|---|---|
| 1 | `references/assessment/tasks/grade/ingest_quiz.md` | every source into one results CSV: report workbooks, leaderboard HTML, screenshots |
| 2 | `references/assessment/tasks/grade/score_quiz.md` | the results CSV to one score per trainee per quiz |
| 3 | `references/assessment/tasks/grade/export_fams_theory.md` | the scores as FAMS's theory mark template, `--quiz-scores` |

A multiple-choice theory exam goes the same way, as a module with one quiz: at
step 3, give it its code on FAMS with `--assessment`. FAMS imports quizzes and
the theory exam from the same theory mark template.

## Report

Per quiz: how many scored out of the active roster and who has no score; every
unmatched nickname and what you did with it; who was left out of the FAMS
workbook and who was written as 0; and the three output paths.
