# Workflow — quiz scores

A module's quiz results, from wherever they came, to scores out of 10 and the
workbook FAMS imports — not the assignment pipeline: no preprocessing, no
batches, no score sheets. Run it once per module (JCF, SBAD…), over all of that
module's quizzes at once.

| Step | Task | Notes |
|---|---|---|
| 1 | `references/assessment/tasks/grade/ingest_quiz.md` | every source into one results CSV: report workbooks, leaderboard HTML, screenshots |
| 2 | `references/assessment/tasks/grade/score_quiz.md` | the results CSV to one score per trainee per quiz |
| 3 | `references/assessment/tasks/grade/export_fams.md` | the scores as the FAMS import workbook |

`references/assessment/tasks/grade/merge_quizzes.md` lines up the output of the
single-quiz `grade quiz` command; this workflow does not need it.

## Report

Per quiz: how many scored out of the active roster and who has no score; every
unmatched nickname and what you did with it; who was left out of the FAMS
workbook and who was written as 0; and the three output paths.
