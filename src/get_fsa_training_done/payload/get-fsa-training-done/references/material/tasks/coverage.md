# Task — Find what material is missing

Compare what the session plan names with what the folder holds.

## Inputs

| Input | Notes |
|---|---|
| `schedule` | the topic's ScheduleDetail CSV |
| `materials_dir` | the module's folder |
| `syllabus` | optional; adds the objective-code checks |

## Produces

A list of gaps, by rule.

## Steps

```bash
FSA material coverage --schedule "<TOPIC>_ScheduleDetail.csv" \
  --dir "<materials_dir>" --syllabus "<TOPIC>_Syllabus.md"
```

- `MAT-C01` (error): the plan names a file that does not exist — a session with
  nothing to deliver.
- `MAT-C02` (warning): a file no session uses.
- `MAT-C03`/`C04`: objective codes that disagree with the plan or the syllabus.
- Quizzes, briefs, exams and rubrics are reported as *owned by another
  feature*, never as missing here.

## Done when

Every `MAT-C01` is either written or handed to the feature that owns it.

## Hands off to

`references/material/tasks/write_lab.md` or
`references/material/tasks/write_lecture.md` — the session row already
specifies the gap. Never invent material the plan did not ask for: if the
module needs a session that is not there, the program feature changes the plan
first.
