# Material — overview

Writes the teaching material a session plan calls for, and checks that what the
plan promises exists.

Read this before any material workflow or task: it holds the commands and the
rules every one of them assumes. Each task lists its own inputs, and each
document serves a session — find the row in the topic's ScheduleDetail CSV that
names it before writing a line.

## What this feature does not own

A session row in a programme's plan names the file that serves it. Producing
*that file* is this feature's job when it is teaching material, and someone else's
otherwise.

| Artifact | Feature |
|---|---|
| quiz questions, assignment briefs, exams, rubrics, grading | the assessment feature |
| session plans, syllabi, schedules, module structure | the program feature |
| lecture notes, handbooks, appendices, lab guides and their worksheets | this one |

A lab guide is the guided middle: shorter than an assignment, step-numbered,
checkable by the learner. If it carries marks and a rubric it is an assignment,
and it belongs to the assessment feature. Say so rather than writing it here.

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
- **Written for the trainee.** Direct, plain, and never trainer notes; see
  `references/material/conventions.md` and `references/common/style.md`.
- **English by default.** A translation is a separate file whose stem ends
  `_vn`, never a rewrite of the original — everything else links to the original.
  Write it with `references/common/tasks/translate_vn.md`.
- **Report measurements, not impressions.** "12 of 12 notes pass, 3 labs the
  plan names are missing" is a measurement.
- **Do not invent work the plan did not ask for.** If a module needs a session
  that is not there, the session plan changes first, and that belongs to
  the program feature.

## Step 2 — Report back

List every file written with its full path and the session it serves, the
`FSA material verify` result with its rule ids, and — when material was missing
— which of the gaps belong to another feature.
