# Workflow — grade submissions

For assignments and exams: **preprocess → plan → score in parallel batches →
aggregate → export to FAMS.** The commands do the mechanical work; the
judgement is yours.

| Step | Task | Notes |
|---|---|---|
| 1 | `references/assessment/tasks/grade/preprocess.md` | echo the resolved absolute paths and wait for a go-ahead first |
| 2 | `references/assessment/tasks/grade/plan_batches.md` | default 4 batches |
| 3 | `references/assessment/tasks/grade/score_submissions.md` | one subagent per batch when there are more than a handful |
| 4 | `references/assessment/tasks/grade/aggregate.md` | grade CSV and legend |
| 5 | by type: `references/assessment/tasks/grade/export_fams_practice.md` for an assignment or the practice exam; `references/assessment/tasks/grade/export_fams_theory.md` (`--grades`) for a written theory exam | from the class template or the roster; skip it for a retake, which exports after the merge |

## Report

How many were graded, who did not submit, any UNKNOWN-ID or extraction failure
still open, the score distribution, the paths to the CSV and its legend, and
the FAMS workbook with who it left out or wrote as 0.

Do not run the cheat checks unless asked —
`references/assessment/workflows/grade/cheat_check.md` is a separate workflow
with a separate purpose.
