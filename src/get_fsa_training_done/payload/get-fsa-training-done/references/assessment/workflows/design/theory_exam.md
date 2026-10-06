# Workflow — theory exam

A graded written exam, not a live game. Everything from `quiz.md` applies to the
master CSV; this file covers what differs.

**Produces:** `<stem>.csv` (instructor-only master), `<stem>_coderbyte.json`

Read `references/assessment/workflows/design/quiz.md` first for the master CSV rules, then
apply the differences below.

## What changes

### Timing

A theory exam gives real thinking time. Take the time map from the level's
non-quiz timings in `references/assessment/levels.md` — typically Easy 30s, Medium 45s,
Hard 75s — not the quiz's 5/10/20, which exist for a live buzzer format.

### Question depth

Because the marks count, questions have to discriminate rather than merely
cover. Apply the level's Bloom mix strictly: at `UP_SKILL` and above, most
questions are Apply and Analyze, which means scenario stems — a situation, a
symptom, a decision — rather than definition recall.

A recall question dressed in a scenario is still a recall question. If the
candidate can answer without reading the scenario, it is not an Apply question.

### Delivery format

```bash
FSA assessment emit coderbyte --master "<output_dir>/<stem>.csv" \
                   -o       "<output_dir>/<stem>_coderbyte.json"
```

Coderbyte marks answers by *position*, and **index 0 is always correct** —
whether or not it appears in `correctAnswers`. The vendor template shows this in
its own answer text: `correctAnswers: ["2", "3"]` over answers
`["I am correct", "Wrong 2", "Will be correct", "Will be correct"]` means 0, 2
and 3 are correct, not just 2 and 3.

So `correctAnswers` *adds to* index 0 rather than replacing it. The emitter
therefore always puts a correct option first, and for a multi-answer question
lists every correct index — which means `"0"` is always among them.

Never hand-write this file. Listing the real answer indices while leaving a
wrong option at index 0 marks that wrong option correct, the import accepts it
without complaint, and the first sign of trouble is candidates scoring on an
answer that was never right.

`references/assessment/coderbyte_mc_import_template.json` shows the shapes.

## Verify

```bash
FSA assessment verify --type theory_exam \
  --master    "<output_dir>/<stem>.csv" \
  --coderbyte "<output_dir>/<stem>_coderbyte.json" \
  --level     "<LEVEL>"
```

`--level` (`UP_SKILL:mid` for a banded level) supplies the non-quiz time map
and checks the Bloom and difficulty mix against the level as a warning. Pass
`--time-map` only when the confirmed map differs from the level's.

Then run `references/assessment/verifiers/theory_exam.md`.
