# Task — Verify a programme

Reconcile every artifact against the others.

## Inputs

| Input | Notes |
|---|---|
| `program_dir` | the programme's folder |
| policy flags | only where they differ from the defaults |

## Produces

PASS or FAIL, the derived facts, and findings by rule id.

## Steps

```bash
FSA program verify --program-dir "<program_dir>" [--topic CODE] [--json]
```

1. Read the derived facts first: module count, totals, training day, week and
   day columns. A training day of 257 minutes says the totals disagree before
   any rule fires.
2. Fix findings by rule id; `references/program/rules.md` explains each.
   **Errors** mean the artifacts contradict each other; **warnings** may be
   deliberate, and `--strict` promotes them.
3. Usually deliberate: `PRG-S08` for a project module grouped by sprint (pass
   `--max-sessions-per-chapter inf`), `PRG-S13` for a one-quiz topic, `PRG-S17`
   for someone else's programme (drop `--creator`), `PRG-X05` when the code's
   level segment is not the audience's.
4. Flags: `--topic`, `--first-weekday`, `--pass-mark N`, `--item-pattern
   "Item=REGEX"`, `--minutes-per-day N`.
5. A missing quiz or exam file is the assessment feature's; a missing lecture
   or lab is the material feature's. Name the owner; do not write it here.

## Done when

PASS, with every warning fixed or named as deliberate.

## Hands off to

The report back in `references/program/overview.md`.
