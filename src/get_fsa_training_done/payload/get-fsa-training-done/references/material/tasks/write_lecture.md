# Task — Write the lecture note

The module in one file: the first page a trainee opens, the way through the
module, its theory condensed, and what they keep as a reference and revise from
before the theory exam or a job interview. One note per module, not per session
— the decks teach each lesson, the note is what stays. It also holds what older
modules split into a handbook and an appendix.

## Inputs

| Input | Notes |
|---|---|
| `materials_dir` | the module's folder; never assumed |
| `schedule` | the topic's ScheduleDetail CSV: the lessons in order; every row the note serves names it |
| `syllabus` | the topic's syllabus, for the syllabus map |
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
   and nothing beyond them. Run `FSA material init --dir "<materials_dir>"` if
   `_theme/` is missing.
2. Start from `references/material/templates/lecture_note.html`; the parts and
   their order are in `references/material/structure.md` and `verify` checks
   them.
3. **The way through the module**, first:
   - **Module Map**: one row per lesson, in order, linking its deck, its topic
     below (`#<topic-id>`) and its lab. A file not written yet is listed
     without a link.
   - **How to Study This Module**: the routine per lesson — slides in the room,
     the lesson's topic here after, then the lab — and how to revise from this
     note before the theory exam or an interview.
   - **Environment Setup**, when there is anything to install: pinned to
     versions, with a command that proves each piece works.
   - **The Running Example**: the one domain the lessons share, so every
     example composes instead of resetting.
4. **One `topic` part per lesson**, in the order of its deck, with an `id` the
   module map, the syllabus map and the labs link to. **Condense, do not
   retell**: the definitions, the rules and why they hold, the smallest example
   that shows each, and a comparison table wherever two things are easily
   confused. One `<h3>` per point; prose before any example (`MAT-D27`). No
   step-by-step walkthroughs and no exercises — those are the deck's check
   slides and the lab's.
5. **Common Misconceptions**: one `<h3>` per wrong belief, said the way a
   trainee would say it, then what is true and how to tell.
6. The summary has one item per objective: the page to reread the night before.
7. **Review Questions**: the questions a theory exam or an interviewer asks —
   definitions, why, when, compare, what goes wrong — at least two per topic and
   five in all (`MAT-D09`). Every question carries `data-objective` and a model
   answer in `<details>`, with its reason; every objective is asked about
   (`MAT-D25`, `MAT-D26`).
8. The **Glossary**, when the module has terms worth a `<dl>`.
9. The **Full Syllabus Map** is derived, never typed:
   `references/material/tasks/derive_syllabus_map.md`.
10. Draw diagrams by `references/material/conventions.md` § Diagrams.

## Done when

`FSA material verify "<materials_dir>"` reports no errors for the note — run it
over the folder, since `MAT-D32` (one note per module) only makes sense across
it — and the syllabus map is current.

## Hands off to

`references/material/tasks/review_for_trainee.md` before publishing, then
`references/material/tasks/export.md` for the PDF.
