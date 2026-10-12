# Task — Write the lecture note

The module's theory, condensed into one file: what a trainee keeps as a
reference and revises from before the theory exam or a job interview. One note
per module, not per session — the decks teach each lesson, the note is what
stays.

## Inputs

| Input | Notes |
|---|---|
| `materials_dir` | the module's folder; never assumed |
| `schedule` | the topic's ScheduleDetail CSV; every lecture row names the note |
| the file name | `<subject>_lecture_note.html`, the subject code the labs use (`dbf_lab_01.html` → `dbf_lecture_note.html`) |
| the decks | `NN_Topic_Name.deck.html`, the lessons the note condenses, in index order |
| the approved outline | from `references/material/tasks/propose_outline.md` |

## Produces

`<subject>_lecture_note.html` in `materials_dir`, and its `.pdf` once exported.
It is handed out as the HTML and the PDF only — never a `.pptx`.

## Steps

1. **Outline first.** Without an approved outline for this note, stop and run
   `references/material/tasks/propose_outline.md`; write nothing until the user
   approves it. The note serves the objectives of every session that names it,
   and nothing beyond them.
2. Start from `references/material/templates/lecture_note.html`; the parts and
   their order are in `references/material/structure.md` and `verify` checks
   them. One `topic` part per lesson, in the order of its deck, with an `id` the
   handbook and the appendix can link to.
3. **Condense, do not retell.** Each topic holds what an examiner or an
   interviewer asks about: the definitions, the rules and why they hold, the
   smallest example that shows each, and a comparison table wherever two things
   are easily confused. One `<h3>` per point; prose before any example
   (`MAT-D27`). No step-by-step walkthroughs and no exercises — those are the
   deck's check slides and the lab's.
4. **Common Misconceptions**: one `<h3>` per wrong belief, said the way a
   trainee would say it, then what is true and how to tell.
5. The summary has one item per objective: the page to reread the night before.
6. **Review Questions**: the questions a theory exam or an interviewer asks —
   definitions, why, when, compare, what goes wrong — at least two per topic and
   five in all (`MAT-D09`). Every question carries `data-objective` and a model
   answer in `<details>`, with its reason; every objective is asked about
   (`MAT-D25`, `MAT-D26`).
7. Draw diagrams by `references/material/conventions.md` § Diagrams.

## Done when

`FSA material verify "<materials_dir>"` reports no errors for the note — run it
over the folder, since `MAT-D32` (one note per module) only makes sense across
it.

## Hands off to

`references/material/tasks/review_for_trainee.md` before publishing, then
`references/material/tasks/export.md` for the PDF.
