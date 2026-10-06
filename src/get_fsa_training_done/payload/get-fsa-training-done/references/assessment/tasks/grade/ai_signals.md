# Task — Collect AI-authorship signals

**Instructor-only.** Gather observable signals that a submission was generated,
for a human to weigh.

## Inputs

| Input | Notes |
|---|---|
| `_preprocessed` | one or more classes |
| `_scores` and a minimum score | to narrow the run to where the question arises |
| the assessment's rules | an assignment that allows AI has nothing to report here |

## Produces

`<results_dir>/_ai_cheat/`: signals per submission.

## Steps

```bash
FSA assessment grade ai-cheat --preprocessed "<submissions_dir>/_preprocessed" \
  --subject "<SUBJECT>" --type "<TYPE>" --scores "<results_dir>/_scores" \
  --min-score 6.0 --out "<results_dir>/_ai_cheat"
```

| Signal | Weight |
|---|---|
| Non-keyboard characters (em dash, arrow, curly quotes) | Strong — they arrive by paste; check for an IDE's smart punctuation |
| Comment narration — comments restating the code or the brief beneath them | Strong |
| Comment-to-code ratio, Javadoc volume | Contextual; compare against the cohort |
| Clustered modification times | Weak |
| Byte- or token-identical files across submissions | Strong, but a shared-source signal, not an AI one |

## Done when

Each flagged submission has its evidence quoted and a confidence stated.

## Hands off to

`references/assessment/workflows/grade/cheat_check.md` § Report.
