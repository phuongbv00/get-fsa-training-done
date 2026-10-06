# Workflow — read a verification report

```bash
FSA program verify --program-dir "<program dir>"
FSA program verify --program-dir "<program dir>" --json    # for machine use
```

## What comes back

A `PASS` or `FAIL` line, the derived facts, and one line per finding:

```
ERROR: [PRG-S09] HN_FR_JSKS_DBF_Syllabus.md: Concept/Lecture: says 25.00% but the
       session plan gives 20.83% (150 of 720 minutes)
```

Every finding names its rule. `references/program/rules.md` explains what that rule
checks and why it exists.

**Errors** mean the artifacts contradict each other. **Warnings** mean something
looks wrong but may be deliberate; the run still passes. `--strict` promotes
them.

## The derived facts are the point

The report prints the module count, the totals, the length of a training day and
the week and day column counts because they were **computed from the sources**,
not assumed. Read them: a training day of 257 minutes says the totals disagree,
long before any individual rule fires.

## Warnings that are usually deliberate

| Rule | When it is fine |
|---|---|
| `PRG-S08` chapter spans too many sessions | a capstone groups a chapter by sprint — pass `--max-sessions-per-chapter inf` |
| `PRG-S13` quizzes in one chapter | a one-quiz topic |
| `PRG-S17` creator mismatch | the programme was authored by someone else; drop `--creator` |
| `PRG-X05` audience disagrees with the level | the code's level segment is not the audience's |

## Findings that belong to another feature

`verify` reports the *slot*. If a session names `dbf_quiz_01.csv` and that file
does not exist, the missing thing is an assessment instrument: say so and name
the assessment feature. A missing `*_lecture_*.md` or `*_lab_*.md` belongs to
the material feature. Do not write either here.

## Useful flags

| Flag | For |
|---|---|
| `--topic CODE` | one topic, skipping the programme-level rules |
| `--first-weekday` | a programme whose first day column is not a Monday |
| `--pass-mark N` | a pass threshold other than 6 |
| `--item-pattern "Item=REGEX"` | an assessment item the default matcher does not know |
| `--minutes-per-day N` | override the derived training day |
