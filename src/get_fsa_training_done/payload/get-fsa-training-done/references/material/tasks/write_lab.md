# Task — Write a lab guide

The guided practice a session plan asks for: shorter than an assignment,
step-numbered, and checkable by the trainee without a marker.

## Inputs

| Input | Notes |
|---|---|
| `materials_dir`, `schedule` | as for a lecture note |
| the session row | the file name, the minutes, the objective codes, the `Content` line |

## Produces

`<subject>_lab_NN.md`, and `<subject>_lab_NN_worksheet.md` when groups run it.

## Steps

1. Count the steps against the minutes before writing them: a lab that cannot
   be finished in its time is the commonest failure here.
2. Shape: `references/material/templates/lab_guide.md`. `verify` enforces
   `**Duration:** N min`, `## Objectives` citing the session's codes, `## Steps`
   as an ordered list, and `## Acceptance` as `- [ ]` items.
3. Each step ends in something the trainee can *see*: a passing test, a rendered
   page, a row in a table, a logged value.
4. Give the starting state in `## Before you start`, and name any starter
   project or worksheet and where it comes from.
5. Every acceptance item is observable by the trainee. "Uses dependency
   injection correctly" is a marker's judgement; "`GET /books` returns the
   seeded rows" is an acceptance item.
6. If it carries marks, a rubric or a deadline, it is an assignment: say so and
   hand it to the assessment feature instead.

## Done when

`FSA material verify "<file>" --type lab` and `FSA material coverage` report no
errors for it.

## Hands off to

`references/material/tasks/write_worksheet.md` for a group lab, then
`references/material/tasks/review_for_trainee.md`.
