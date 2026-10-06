# Task — Aggregate the grades

Roll the score sheets into one grade CSV for the class.

## Inputs

| Input | Notes |
|---|---|
| `<results_dir>/_scores` | the score sheets |
| `roster` | names and row order |

## Produces

`<results_dir>/<subject_lower>_<archive_token>_grades.csv` and its
`.legend.txt`, which maps `T1..TN` back to task ids. Keep them together.

## Steps

```bash
FSA assessment grade aggregate --scores "<results_dir>/_scores" \
  --roster "<roster>" --out "<results_dir>/<subject_lower>_<archive_token>_grades.csv"
```

Dropped trainees are excluded; `--include-dropped-ids <ID>...` names one to keep.

## Done when

The CSV has a row per graded trainee in roster order, and the legend is beside
it.

## Hands off to

`references/assessment/tasks/grade/merge_retake.md` when this was a retake;
otherwise the report.
