# Task — Score submissions

Grade each submission against the rubric and write its score sheet. This is
the judgement half of grading; every other grading task is arithmetic.

## Inputs

| Input | Notes |
|---|---|
| `brief_path`, `rubric_path` | the assessment being graded |
| a batch of folders | from `references/assessment/tasks/grade/plan_batches.md` |
| comment language | English unless the user asks for another |

## Produces

`<results_dir>/_scores/<StudentID>.json` per submission, in the shape of
`references/assessment/score_sheet_schema.md`.

## Steps

1. Read the brief, the rubric and `references/assessment/score_sheet_schema.md`.
   Give each grading subagent the same three, plus its folder list.
2. Read the submission as evidence. **Never run its code on this machine.**
   When the rubric names a behaviour check — the supplied seed test against the
   submitted schema, the starter's tests against the submitted code — run it
   through `references/common/tasks/run_in_sandbox.md`. Its result confirms or
   refutes what reading found; it never replaces reading, and a submission that
   does not build is still read and scored for what it contains.
3. Score each task 0-10 and fold that task's caps and deductions into it — its
   `### Tn` subsection and `### Every task`. Nothing is subtracted from the
   total afterwards.
4. Hold to the grading conventions:
   - **Correct and small beats broken and broad.** Three tasks done properly
     outscore five half-done.
   - **Claims count only when the work backs them.** A README saying a feature
     exists is not the feature.
   - **Content over form.** A wrong file name, a missing `mermaid` fence around
     a correct diagram, or a different but valid layout loses nothing unless the
     rubric makes it a criterion.
   - When it is unclear who did the work (a resolved conflict, a shared commit),
     credit what the submission shows; integrity is a separate question.
5. Write **one or two sentences per task**, learner-facing, about the work:
   - in the requested language, following `references/common/style.md` (and
     `references/common/language_vn.md` for Vietnamese — never "của bạn");
   - never the grading method ("could not run it", "static review"), never
     arithmetic, never a suspicion of copying or AI use.
6. Check the arithmetic: `total = sum(score * weight) / 100`, every score 0-10.

## Done when

Every folder in the batch has a score sheet whose total recomputes exactly.

## Hands off to

`references/assessment/tasks/grade/aggregate.md`.
