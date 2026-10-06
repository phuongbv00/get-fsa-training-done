# Task — Derive the time allocation

Recompute a syllabus's section 8 from its session plan. Never type the
percentages.

## Inputs

| Input | Notes |
|---|---|
| the session plan | `<TOPIC>_ScheduleDetail.csv` |
| the syllabus | `<TOPIC>_Syllabus.md` |

## Produces

Section 8 of the syllabus, rewritten.

## Steps

```bash
FSA program derive allocation --schedule "<plan>" --syllabus "<syllabus>" --write
FSA program derive allocation --schedule "<plan>" --syllabus "<syllabus>" --check
```

`--check` writes nothing; exit 1 means the syllabus no longer matches its plan.

## Done when

`--check` exits 0.

## Hands off to

`references/program/tasks/verify.md`.
