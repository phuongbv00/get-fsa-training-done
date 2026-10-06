# Workflow — author a topic

**Produces:** `syllabi/<TOPIC>_Syllabus.md` and `syllabi/<TOPIC>_ScheduleDetail.csv`.

## 1. The session plan comes first

It is the document everything else in the syllabus is derived from, so write it
before the syllabus prose. `references/program/schemas.md` has the exact header.

Per row: the unit number and chapter name, the session number, what happens,
the objective codes it serves, the delivery type, the minutes, `Blended`, and
the file that serves it.

Constraints the verifier enforces:

- Total minutes = the topic's days × the length of a training day.
- No session runs longer than a training day.
- A session belongs to exactly one chapter.
- Every objective code cited must be defined in the syllabus.

Name the serving file in the materials column even when it does not exist yet —
that is how the other two features know what to produce.

## 2. Write the syllabus around it

The section order is fixed, because the workbook writes each section to a
hard-coded cell range. Do not add sections; one the form has no cell for is
dropped silently on export, so the verifier treats it as an error.

`references/program/examples/mini/` is a small, complete, correct programme. Follow its
shape.

## 3. Derive section 8

Never type the percentages.

```bash
FSA program derive allocation \
  --schedule "syllabi/<TOPIC>_ScheduleDetail.csv" \
  --syllabus "syllabi/<TOPIC>_Syllabus.md" --write
```

## 4. The assessment scheme

Weights must sum to 100, `Pass Criteria` is last with a count and **no** weight,
and every item's count must equal the number of occurrences the session plan
delivers.

An occurrence is the item plus its ordinal, so a long assignment spread over
kickoff, completion and acceptance rows is *one* assignment, and a final review
run in two parts is *one* review — while `Quiz 1` and `Quiz 2` are two quizzes.

## 5. Verify

```bash
FSA program verify --program-dir "<program dir>" --topic "<TOPIC>"
```
