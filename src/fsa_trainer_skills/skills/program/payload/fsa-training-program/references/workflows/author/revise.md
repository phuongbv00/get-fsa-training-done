# Workflow — change a session plan

Changing a plan changes several derived figures at once. Work outward, and
re-derive rather than re-typing.

## The cascade

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

Most edits stop at the first line. An edit that changes the *total* minutes
reaches the bottom, and every step below is an error the verifier reports rather
than something to discover later.

## Order of work

1. Edit the plan.
2. `FSA program derive allocation --write` for that topic.
3. `FSA program verify --program-dir <dir>` and read the findings.
4. If the day count changed, update the module table and the day grid, then
   verify again.
5. Re-export any workbook you had already produced — it holds the old numbers.

## Checking without changing anything

```bash
FSA program derive allocation --schedule <plan> --syllabus <syllabus> --check
```

Exit code 1 means the syllabus no longer matches its plan.
