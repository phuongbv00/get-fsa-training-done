# Workflow — grade a retake

A retake is graded like any paper, into its own results folder, then merged
with the first attempt under the retake policy.

| Step | Task | Notes |
|---|---|---|
| 1 | `references/assessment/workflows/grade/submissions.md` | against the **retake** paper's brief and rubric, into a separate `results_dir` |
| 2 | `references/assessment/tasks/grade/merge_retake.md` | first-attempt CSV + retake CSV → merged CSV; confirm cap, keep policy and voided retakes |
| 3 | by type, as in `references/assessment/workflows/grade/submissions.md` step 5: `references/assessment/tasks/grade/export_fams_practice.md` or `references/assessment/tasks/grade/export_fams_theory.md` | the merged CSV, against the retake's FAMS assessment code |

## Report

The merged CSV's path, who kept the retake, who was capped, whose retake was
voided, that the two per-attempt CSVs are unchanged beside it, and the FAMS
workbook.
