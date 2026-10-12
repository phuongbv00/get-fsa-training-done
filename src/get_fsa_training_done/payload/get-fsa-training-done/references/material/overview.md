# Material — overview

Writes the teaching material a session plan calls for, and checks that what the
plan promises exists.

Material is HTML on the FSA theme — the slide template's layouts, colours and
backgrounds — one file per artifact. The HTML is the source of truth; the
`.pptx` and `.pdf` handed out are exported from it. In order of how much a
trainee learns from them, a lesson has:

| Kind | File | Read where |
|---|---|---|
| slide deck | `NN_Topic_Name.deck.html`, one per lesson | in the session, presented from the browser or the exported `.pptx` |
| module handbook | `00_Study_Guide_Handbook.html` | first, and whenever lost |
| lecture note | `<subject>_lecture_note.html`, **one per module** | after each session, and to revise before the theory exam or an interview — handed out as the HTML and its `.pdf` |
| lab guide | `<subject>_lab_NN.html` | in the lab session |

A recorded video is a later addition: a deck's speaker notes are written so they
can become its script.

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
| slide decks, lecture notes, handbooks, appendices, lab guides and their worksheets | this one |

A lab guide is the guided middle: shorter than an assignment, step-numbered,
checkable by the learner. If it carries marks and a rubric it is an assignment,
and it belongs to the assessment feature. Say so rather than writing it here.

## Commands

| Command | Does |
|---|---|
| `FSA material init --dir DIR` | put the theme in `DIR/_theme/`, which every page links |
| `FSA material verify PATH...` | check documents against the shape their names claim |
| `FSA material coverage --schedule CSV --dir DIR` | what the plan asks for versus what exists |
| `FSA material derive appendix --syllabus MD --dir DIR --appendix HTML --write` | rebuild the appendix's syllabus map |
| `FSA material export pptx\|pdf FILE` | derive the `.pptx` (a deck) or `.pdf` from the HTML |

## Standing rules

- **Outline first, always.** Before any document is created or overwritten,
  its outline is shown and explicitly approved:
  `references/material/tasks/propose_outline.md`. No draft file "to show what it
  would look like". Exports, `verify`, `coverage` and refreshing a derived map
  write no document and need no outline.
- **Write to the session, not to the topic.** A deck or a lab covering more
  than the session it serves is one that session cannot deliver. The lecture
  note is the exception by design: it condenses the whole module, and serves
  the objectives of every session that names it — no more.
- **One lecture note per module** (`MAT-D32`): the module's theory, condensed,
  for revising before the theory exam or an interview. Its topics follow the
  decks; it does not retell them, and it has no exercises.
- **The syllabus map is derived, never typed.** Its deep anchors break silently
  when a heading is renamed.
- **Written for the trainee.** Direct and plain; see
  `references/material/conventions.md` and `references/common/style.md`. A
  deck's speaker notes are the one place written to the trainer.
- **The theme decides how it looks.** No inline styling, no colours or fonts of
  a page's own: a module then reads as one, in light and dark mode, and exports
  cleanly.
- **Exports are outputs.** Never edit a `.pptx` or `.pdf` by hand; change the
  HTML and export again.
- **One declared language per module.** `<html lang>` says it — `en` by
  default, `vi` for a module written in Vietnamese — and the theme and the
  exporters write their own words in it. A translation of an English original
  is a separate file ending `_vn`; see `references/material/conventions.md`
  § Language.
- **Report measurements, not impressions.** "12 of 12 decks pass, 3 labs the
  plan names are missing" is a measurement.
- **Do not invent work the plan did not ask for.** If a module needs a session
  that is not there, the session plan changes first, and that belongs to
  the program feature.

## Report back

List every file written with its full path and the session it serves, the
`FSA material verify` result with its rule ids, and — when material was missing
— which of the gaps belong to another feature.
