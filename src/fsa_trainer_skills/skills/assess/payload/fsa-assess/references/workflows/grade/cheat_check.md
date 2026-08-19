# Workflow — copying and AI-authorship checks

**Instructor-only. Run only when the user explicitly asks.** Never as part of a
normal grading run.

Two different questions, kept apart because the evidence for each is different:

| Question | Command |
|---|---|
| Did these two share a source? | `FSA grade plagiarism` |
| Was this written by an AI? | `FSA grade ai-cheat` |

## The rule that governs everything here

**No signal from this workflow may change anyone's grade, and none of it may
reach a learner.**

- Do not zero, reduce, or cap a submission because of a similarity score.
- Do not put a suspicion in a score sheet comment or a grade CSV.
- Do not tell a trainee they were flagged.

The output is a ranked list for a human to review, ideally alongside an oral
check. Nothing here is proof.

## 1. Similarity between submissions

```bash
FSA grade plagiarism \
  --preprocessed "<submissions_dir>/_preprocessed" \
  --subject "<SUBJECT>" --type "<TYPE>" \
  --out     "<results_dir>/_plagiarism"
```

Winnowing fingerprints, compared only within a language family. Comments and
string literals are stripped first, so renaming variables and reformatting does
not hide a copy.

Two numbers per pair:

- **similarity** (Jaccard) — how much of their combined work is shared;
- **containment** — how much of the *smaller* submission appears in the larger.
  This is the one that catches "copied a subset", where a low similarity hides a
  wholesale lift into a bigger project.

Widen the net with `--threshold 0.4`, narrow it with `--threshold 0.6`.

**Reading the result:** a shared schema file or a scaffold everyone was given
will flag legitimately. Look at the evidence file pair before concluding
anything — the report names the two files sharing the most fingerprints.

## 2. AI-authorship signals

```bash
FSA grade ai-cheat \
  --preprocessed "<submissions_dir>/_preprocessed" \
  --subject "<SUBJECT>" --type "<TYPE>" \
  --scores  "<results_dir>/_scores" \
  --min-score 8.0 \
  --out     "<results_dir>/_ai_cheat"
```

`--scores` with `--min-score` narrows the run to high-scoring submissions, which
is usually where the question actually arises.

What it collects, and how much each is worth:

| Signal | Weight |
|---|---|
| Non-keyboard characters (em dash, arrow, curly quotes) | Strong — these arrive by paste. But an IDE's smart-punctuation can produce the dash and quote forms, so check the editor before concluding |
| Comment narration — comments that restate the identifiers beneath them | Strong; humans rarely write these at volume |
| Comment-to-code ratio, Javadoc volume | Contextual; compare against the cohort, not an absolute |
| Clustered modification times | Weak — archive and copy tools normalise timestamps |
| Placeholders alongside generated output | Contextual |
| Byte-identical or token-identical files across submissions | Strong, but this is a *shared-source* signal, not an AI one |

## 3. Keep the two conclusions separate

The most common mistake is collapsing them. "This looks AI-written" and "these
two came from the same source" are different findings with different
consequences, and a submission can show one without the other.

Report them as separate confidence judgements, each with the evidence behind it,
and say plainly what you are *not* confident about.

## 4. Report

Give the user a ranked list, the evidence for each entry, and a recommended
verification step — usually an oral check on a specific part of their own
submission. Say explicitly that nothing here has been applied to any grade.
