# Task — Fill the schedules

Put in what the module table cannot know.

## Inputs

| Input | Notes |
|---|---|
| the four skeleton CSVs | from `references/program/tasks/derive_skeleton.md` |
| outcome standards | the programme's OST list |

## Produces

The four CSVs, filled.

## Steps

- **MasterSchedule** — exactly one `Mark` per row, in that module's assessment
  week.
- **DetailedSchedule** — hours per day. Each row's cells total its `Drt (h)`;
  the grid totals the programme's hours; the days carrying teaching equal the
  programme's day count; weekend columns stay empty.
- **TopicList** — topic names match the module table exactly.
- **OSTModuleMapping** — one row per outcome standard, `x` under every module
  that delivers it. Every outcome is mapped somewhere.

## Done when

`FSA program verify --program-dir "<program_dir>"` reports no schedule findings.

## Hands off to

`references/program/tasks/write_syllabus.md`, once per module.
