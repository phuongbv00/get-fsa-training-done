# Task — Derive the schedule skeletons

Write the four CSVs' headers and row order from the module table. Never type
them by hand.

## Inputs

| Input | Notes |
|---|---|
| the curriculum | with an agreed module table |

## Produces

`<PROGRAM>_MasterSchedule.csv`, `_DetailedSchedule.csv`, `_TopicList.csv`,
`_OSTModuleMapping.csv`, with `W1..Wn` and `D1..Dm` sized from the table.

## Steps

```bash
FSA program derive skeleton --curriculum "<PROGRAM>_TrainingProgramCurriculum.md" --out-dir "<program_dir>"
```

## Done when

The four files exist with one row per module, in order.

## Hands off to

`references/program/tasks/fill_schedules.md`.
