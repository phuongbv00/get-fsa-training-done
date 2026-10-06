# Task — Plan the grading batches

Split the preprocessed folders into batches for parallel grading, skipping
anyone already scored.

## Inputs

| Input | Notes |
|---|---|
| `_preprocessed` | from `references/assessment/tasks/grade/preprocess.md` |
| `results_dir` | score sheets go in `<results_dir>/_scores` |
| batch count | default 4 |

## Produces

A JSON plan on stdout: batches of folder names.

## Steps

```bash
FSA assessment grade plan --preprocessed "<submissions_dir>/_preprocessed" \
  --scores "<results_dir>/_scores" --subject "<SUBJECT>" --type "<TYPE>" \
  --roster "<roster>" --batches 4
```

A re-run picks up exactly the leftovers; `--include-scored` re-grades everyone.

## Done when

Every unscored submission is in exactly one batch.

## Hands off to

`references/assessment/tasks/grade/score_submissions.md`, one batch per
subagent when there are more than a handful.
