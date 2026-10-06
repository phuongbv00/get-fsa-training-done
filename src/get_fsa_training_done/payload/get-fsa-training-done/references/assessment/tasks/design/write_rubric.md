# Task — Write the rubric

The instructor's scoring guide. Every criterion in it must be settleable from
the submitted files by a human or a model, and its task list becomes the key of
every score sheet.

## Inputs

| Input | Notes |
|---|---|
| the brief | `<stem>.md`, finished |
| the level | its rubric posture, from `references/assessment/levels.md` |

## Produces

`<stem>_rubric.md`, **instructor-only**, always in English.

## Steps

1. Read `references/assessment/examples/rubric_example.md` for tone and depth,
   and `references/assessment/grading_contract.md` when `grade_pipeline` is yes.
2. Write six sections, in order:

   ```markdown
   # <Type> Rubric (INSTRUCTOR ONLY) - <Name>

   > **Code:** <LEVEL>_<SUBJ>_<ABBR>_<seq>
   >
   > **Learner brief:** [<stem>.md](<stem>.md)
   >
   > WARNING: **DO NOT distribute this file to learners.**

   ---

   ## 1. Grading Principle
   ## 2. Fixed Task List
   ## 3. Per-Task Scoring Guide
   ## 4. Caps and Deductions
   ## 5. Common point-loss reasons
   ## 6. Score sheet
   ```

3. Task ids, names and weights match the brief exactly. Each task's
   sub-criterion table sums to exactly 10.0.
4. Put the **standards** here that the brief deliberately left out: a user
   story's three parts, what makes a WBS item done, which index type is right
   and why. Phrase the mechanism so an equally valid alternative is not punished.
5. For an exam, say in § 1 where the 80/20 line falls — which criteria are the
   ~20% beyond what the labs drilled — and that 8 is the designed ceiling for a
   trainee who only did the labs.
6. For a written exam or quiz, write **one row per question**, with the points a
   strong answer covers. A bare definition with no mechanism or example earns at
   most half the row; correct, equivalent wording earns full credit.
7. When a criterion needs behaviour shown — a seed loads, the tests pass —
   name the check and the supplied file it runs, so the grader runs it through
   `references/common/tasks/run_in_sandbox.md`. Reading the work stays the
   primary evidence.
8. § 4 is one `### Tn - <name>` subsection per task that needs caps, in task
   order, after an optional `### Every task`. Every entry bounds that task's raw
   0-10 score, never the total. Under exam time pressure a missing foundation
   **caps** the task rather than deducting from it.
9. § 6 lists tasks and weights only: no `Caps applied:`, no `Deductions:`.

## Done when

`FSA assessment verify` passes on brief and rubric together (see
`references/assessment/tasks/design/verify.md`).

## Hands off to

`references/assessment/tasks/design/write_answer_template.md` when the
candidate submits writing, then `references/assessment/tasks/design/render_pdf.md`.
