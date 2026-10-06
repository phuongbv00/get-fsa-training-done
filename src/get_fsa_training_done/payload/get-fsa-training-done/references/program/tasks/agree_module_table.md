# Task — Agree the module table

The table every other number in a programme is derived from: each module's
name, code, hours and days, and the TOTAL row.

## Inputs

| Input | Notes |
|---|---|
| `program_dir` | ask; never assume |
| `program_code` | the site, level, track and subject segments, e.g. `HN_FR_JSKS_JAVA_WEB` |
| `program_title`, `role` | the curriculum's heading |
| `modules` | name, code, hours, days for each |

## Produces

`<PROGRAM>_TrainingProgramCurriculum.md` with its module table, schedule
design, training method and audits.

## Steps

1. Read `references/program/artifact_map.md` if you have not.
2. Settle the table before anything else:
   - module rows sum to the TOTAL row;
   - total hours ÷ total days is a whole number of minutes — that number *is*
     the training day (280 hours over 70 days is a 240-minute half-day);
   - a topic code is the programme code with its last segment replaced:
     `HN_FR_JSKS_JAVA_WEB` gives `HN_FR_JSKS_DBF`.
3. Write the curriculum as a standalone programme: what it is, not how it
   differs from an earlier one.
4. Describe the training method as who does what: what the trainer does, what
   the trainee does, and where AI tools are part of the work.
5. Put any audits (an external review after a module) in the schedule design,
   on the days they happen.

## Done when

The user has confirmed the table, and its arithmetic holds.

## Hands off to

`references/program/tasks/derive_skeleton.md`.
