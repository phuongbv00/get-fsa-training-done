# Workflow — write a lab guide

**Produces:** `<subject>_lab_NN.md`.

A lab is the guided middle the session plans ask for: shorter than an
assignment, step-numbered, and checkable by the learner without a marker.

## 1. Read the session row

The plan names the file, the minutes, and the objective codes. A lab that
cannot be finished in its minutes is the commonest failure here, so count the
steps against the time before writing them.

## 2. Shape

`references/templates/lab_guide.md`. What `verify` enforces:

- `**Duration:** N min` — the plan allotted it a length; state it
- an `## Objectives` section citing the codes from the session row
- `## Steps` as an **ordered list**
- `## Acceptance` as `- [ ]` items

## 3. Write the steps

Each step ends in something the learner can *see*: a passing test, a rendered
page, a row in a table, a logged value. A step whose outcome is invisible is a
step they cannot tell they have completed.

Give the starting state in `## Before you start`. If the lab needs a starter
project, name it — and say who supplies it.

## 4. Write the acceptance list

It is the learner's own check, so every item must be observable by them. "Uses
dependency injection correctly" is a marker's judgement; "the app starts and
`GET /books` returns the seeded rows" is an acceptance item.

## 5. Check it

```bash
FSA material verify "<subject>_lab_NN.md" --type lab
FSA material coverage --schedule "<TOPIC>_ScheduleDetail.csv" --dir "<folder>"
```

## Not a lab

If it carries marks, a rubric, or a submission deadline, it is an assignment —
`fsa-training-assessment` writes those. Say so rather than writing it here.
