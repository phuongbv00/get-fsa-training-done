# Material — overview

Writes the teaching material a session plan calls for, and checks that what the
plan promises exists.

Read this before any material workflow or task: it holds the inputs to collect,
the commands, and the rules every material workflow assumes.

## What this feature does not own

A session row in a programme's plan names the file that serves it. Producing
*that file* is this feature's job when it is teaching material, and someone else's
otherwise.

| Artifact | Feature |
|---|---|
| quiz questions, assignment briefs, exams, rubrics, grading | the assessment feature |
| session plans, syllabi, schedules, module structure | the program feature |
| lecture notes, handbooks, appendices, lab guides | this one |

A lab guide is the guided middle: shorter than an assignment, step-numbered,
checkable by the learner. If it carries marks and a rubric it is an assignment,
and it belongs to the assessment feature. Say so rather than writing it here.

## Step 0 — Collect inputs

Ask only for what is missing, and batch the questions.

| Key | Required for | Default |
|---|---|---|
| `materials_dir` | all | ask; never assume |
| `schedule` | authoring, coverage | ask — the topic's ScheduleDetail CSV |
| `syllabus` | objectives checks, the appendix | ask |
| `document_kind` | authoring | infer from the request, then confirm |
| `index` or `lab number` | authoring | derive from what is already in the folder |

**A note serves a session.** Before writing, find the row in the session plan
that names the file: it gives the objective codes, the minutes, and one line
saying what happens. Write to that, and say so in the plan echo.

Before writing anything, report the resolved **absolute** paths, the filename,
and the session it serves. Wait for an explicit go-ahead.

## Commands

| Command | Does |
|---|---|
| `FSA material verify PATH...` | check documents against the template their names claim |
| `FSA material coverage --schedule CSV --dir DIR` | what the plan asks for versus what exists |
| `FSA material derive appendix --syllabus MD --dir DIR --appendix MD --write` | rebuild the appendix's syllabus map |

## Standing rules

- **Write to the session, not to the topic.** A note covering more than the
  session it serves is a note that session cannot deliver.
- **The syllabus map is derived, never typed.** Its deep anchors break silently
  when a heading is renamed.
- **English by default.** A translation is a separate file whose stem ends
  `_vn`, never a rewrite of the original — everything else links to the original.
- **Report measurements, not impressions.** "12 of 12 notes pass, 3 labs the
  plan names are missing" is a measurement.
- **Do not invent work the plan did not ask for.** If a module needs a session
  that is not there, the session plan changes first, and that belongs to
  the program feature.

## Step 2 — Report back

List every file written with its full path and the session it serves, the
`FSA material verify` result with its rule ids, and — when material was missing
— which of the gaps belong to another feature.
