# Workflow — what the plan asks for and what exists

```bash
FSA material coverage \
  --schedule "<TOPIC>_ScheduleDetail.csv" \
  --dir "<materials folder>" \
  --syllabus "<TOPIC>_Syllabus.md"
```

## What it compares

A session plan's materials column names the file that serves each session. That
column is the contract between the three features, and this checks the half that
belongs to teaching material — both directions:

- **`MAT-C01`, an error** — the plan names a file that does not exist. A session
  with nothing to deliver.
- **`MAT-C02`, a warning** — a file exists that no session uses. Unfinished, or
  forgotten, or the plan was written without it.

With `--syllabus` it also checks that the objective codes are ones the syllabus
defines, and that a material mentions the objectives its session claims.

## Files this feature does not own

The plan also names quizzes, assignment briefs, exams and rubrics. Those are
counted and reported as *owned by another feature*, never as missing here — they
belong to the assessment feature.

If a session names a file with a shape this feature does not recognise, it is
counted the same way. Say which feature owns it rather than writing it.

## Turning a gap into work

A missing lab is the usual case, and the session row already specifies it: the
minutes, the objective codes, and a `Content` line saying what the lab does.
Take those to `references/material/workflows/author/lab.md`.

Do not invent a lab the plan did not ask for. If the module needs one, the
session plan is what changes first — and that is the program feature's.
