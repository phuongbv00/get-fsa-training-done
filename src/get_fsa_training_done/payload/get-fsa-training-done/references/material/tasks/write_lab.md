# Task — Write a lab guide

The guided practice a session plan asks for: shorter than an assignment,
step-numbered, and checkable by the trainee without a marker.

## Inputs

| Input | Notes |
|---|---|
| `materials_dir`, `schedule` | as for a slide deck |
| the session row | the file name, the minutes, the objective codes, the `Content` line |
| the approved outline | from `references/material/tasks/propose_outline.md` |

## Produces

`<subject>_lab_NN.html`, and `<subject>_lab_NN_worksheet.html` when groups run it.

## Steps

1. **Outline first.** Without an approved outline for this lab, stop and run
   `references/material/tasks/propose_outline.md`; write nothing until the user
   approves it. The outline counts the steps against the minutes: a lab that
   cannot be finished in its time is the commonest failure here.
2. Start from `references/material/templates/lab_guide.html`. `verify` enforces
   `fsa:minutes`, the objectives with their codes, the steps as an `<ol>`, and
   the acceptance as a `<ul class="checklist">`.
3. Each step ends in what the trainee should *see* — a passing test, a rendered
   page, a row in a table, a logged value — in a `class="expected"` element
   (`MAT-D30`). Where trainees commonly stall, add a
   `<details class="hint">`: a nudge, never the answer.
4. Give the starting state in **Before You Start**, and name any starter project
   or worksheet and where it comes from.
5. Every acceptance item is observable by the trainee. "Uses dependency
   injection correctly" is a marker's judgement; "`GET /books` returns the
   seeded rows" is an acceptance item.
6. Add a **Stretch** for whoever finishes early, so the fastest trainees practise
   rather than wait.
7. If it carries marks, a rubric or a deadline, it is an assignment: say so and
   hand it to the assessment feature instead.

## Done when

`FSA material verify "<file>"` and `FSA material coverage` report no errors for it.

## Hands off to

`references/material/tasks/write_worksheet.md` for a group lab, then
`references/material/tasks/review_for_trainee.md`.
