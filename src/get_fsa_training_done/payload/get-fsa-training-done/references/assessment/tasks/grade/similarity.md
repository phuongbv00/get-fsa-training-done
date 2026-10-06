# Task — Check similarity between submissions

**Instructor-only.** Rank pairs of submissions that may share a source.

## Inputs

| Input | Notes |
|---|---|
| `_preprocessed` | the class's submissions |
| `results_dir` | where the report goes |

## Produces

`<results_dir>/_plagiarism/`: ranked pairs, each with the files sharing the
most fingerprints.

## Steps

```bash
FSA assessment grade plagiarism --preprocessed "<submissions_dir>/_preprocessed" \
  --subject "<SUBJECT>" --type "<TYPE>" --out "<results_dir>/_plagiarism"
```

- **similarity** is how much of the combined work is shared; **containment** is
  how much of the smaller submission appears in the larger, which catches a
  subset lifted into a bigger project.
- A supplied starter, schema or scaffold flags legitimately. Open the evidence
  pair before concluding anything.

## Done when

Every flagged pair has been opened and either explained or kept as a concern
with its evidence.

## Hands off to

`references/assessment/workflows/grade/cheat_check.md` § Report.
