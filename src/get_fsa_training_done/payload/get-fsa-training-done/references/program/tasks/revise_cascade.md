# Task — Change a session plan

Edit a plan and re-derive everything downstream of it, in order.

## Inputs

| Input | Notes |
|---|---|
| the change | what moves, in which topic |
| `program_dir` | the programme it belongs to |

## Produces

The edited plan and every derived figure brought back in line.

## Steps

```
edit the session plan
  └─→ section 8, Time Allocation      FSA program derive allocation --write
  └─→ the topic's day count           if the minutes no longer divide evenly
        └─→ the module's days in the curriculum module table
              └─→ the programme's TOTAL row
                    └─→ the length of a training day
                    └─→ the DetailedSchedule day grid
                    └─→ the week and day column counts
```

1. Edit the plan.
2. `references/program/tasks/derive_allocation.md` for that topic.
3. `references/program/tasks/verify.md`.
4. If the day count changed, update the module table and the day grid, and
   verify again.
5. Re-export any workbook already produced — it holds the old numbers.

## Done when

`verify` passes and every exported workbook is regenerated.

## Hands off to

`references/program/tasks/export_workbook.md` when workbooks exist.
