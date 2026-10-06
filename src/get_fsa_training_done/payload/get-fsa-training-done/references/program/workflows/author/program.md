# Workflow — author a programme

**Produces:** `<PROGRAM>_TrainingProgramCurriculum.md` and the four CSVs beside it.

Read `references/program/artifact_map.md` first if you have not.

## 1. Agree the module table

Everything else is derived from it, so settle it before writing anything else:
each module's name, code, hours and days, and the TOTAL row.

Two rules the verifier enforces:

- The module rows must sum to the TOTAL row.
- Total hours ÷ total days must be a whole number of minutes. That number *is*
  the length of a training day, and every topic is measured against it. A
  programme of 280 hours over 70 days runs a 4-hour technical half-day.

Codes read `SITE_LEVEL_TRACK_SUBJECT`, and a topic code is the programme code
with its last segment replaced — `HN_FR_JSKS_JAVA_WEB` gives `HN_FR_JSKS_DBF`.

## 2. Derive the CSV skeletons

Never hand-type the headers or the row order.

```bash
FSA program derive skeleton --curriculum "<PROGRAM>_TrainingProgramCurriculum.md" --out-dir .
```

That writes the four CSVs with the right columns — including the `W1..Wn` and
`D1..Dm` tails, sized from the module table — and one row per module, in order.

## 3. Fill what the module table cannot know

- **MasterSchedule** — exactly one `Mark` per row, in that module's assessment week.
- **DetailedSchedule** — hours per day. Each row's cells must total its `Drt (h)`,
  the whole grid must total the programme's hours, the number of days carrying
  teaching must equal the programme's day count, and weekend columns stay empty.
- **TopicList** — the topic name must match the module table exactly.
- **OSTModuleMapping** — one row per outcome standard, `x` under every module
  that delivers it. Every outcome must be mapped somewhere.

## 4. Write one syllabus per module

See `references/program/workflows/author/topic.md`.

## 5. Verify

```bash
FSA program verify --program-dir "<program dir>"
```

Fix findings by rule id; `references/program/rules.md` says what each one means and why.
