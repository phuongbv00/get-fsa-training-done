# Task — Write a topic's syllabus and session plan

One module's syllabus and the session plan it is derived from.

## Inputs

| Input | Notes |
|---|---|
| `program_dir` | with its curriculum, for the length of a training day |
| the module | its code, name and days from the module table |
| `creator`, `account`, `unit` | for the authorship block |
| assessment scheme | confirm it; the default is below |

## Produces

`syllabi/<TOPIC>_Syllabus.md` and `syllabi/<TOPIC>_ScheduleDetail.csv`.

## Steps

### 1. The session plan comes first

Header in `references/program/schemas.md`. Per row: unit and chapter, session,
what happens, objective codes, delivery type, minutes, `Blended`, and the file
that serves it. The verifier holds:

- total minutes = the topic's days × the training day;
- no session longer than a training day; a session in exactly one chapter;
- every objective code is defined in the syllabus;
- delivery types come from the vocabulary in `references/program/schemas.md` —
  never an invented label such as "C Concept + Lab".

Name the serving file in the materials column even before it exists: that is
how the material and assessment features know what to produce. Use their file
names (`dbf_lab_01.md`, `dbf_quiz_01.csv`, `dbf_practice_exam_01.md`).

### 2. The syllabus around it

The section order is fixed: the workbook writes each section to a fixed cell
range. Follow `references/program/examples/mini/`. Add no section the template
lacks (no Duration, no Prerequisites — they are dropped on export, so the
verifier treats them as errors).

- **Standalone.** A syllabus can be reused by another programme, so it says
  nothing about the programme around it or an earlier version, and states its
  own days and objectives.
- **Course objectives are yours.** Write the topic's learning outcomes; the
  template's sample rows are format, not content.
- Training format is `Blended` throughout.

### 3. Derive section 8

```bash
FSA program derive allocation --schedule "syllabi/<TOPIC>_ScheduleDetail.csv" \
  --syllabus "syllabi/<TOPIC>_Syllabus.md" --write
```

### 4. The assessment scheme

Weights sum to 100; `Pass Criteria` is last, with a count and no weight; every
item's count equals the occurrences the session plan delivers (an item plus its
ordinal: a long assignment across kickoff and acceptance rows is one; `Quiz 1`
and `Quiz 2` are two).

| Module | Default scheme |
|---|---|
| a taught module | Quiz 10% (one or more, MCQ or written), Assignment 20% (one long, or several short in a foundations module), Final Theory Exam 30%, Final Practice Exam 40% |
| a project module | Sprint Review ×3 60%, Final Review 40%; no quiz or exam |
| pass mark | 6 (`--pass-mark` when the programme differs) |

A project module works in sprints: requirements, design and code all grow each
sprint, and each sprint review grades that increment. Its chapters group the
sprints as one unit ("Sprint 1-3") followed by the final review —
`references/program/examples/capstone/` is the worked example, verified with
`--max-sessions-per-chapter inf`.

## Done when

`FSA program verify --program-dir "<program_dir>" --topic "<TOPIC>"` passes.

## Hands off to

The material and assessment features, for the files the session plan names.
