# Task — Write a slide deck

The slides a session is taught from, on the FSA template. The most effective
material a lesson has, so it is written first; the lecture note then explains in
full what each slide compresses.

## Inputs

| Input | Notes |
|---|---|
| `materials_dir` | the module's folder; never assumed |
| `schedule` | the topic's ScheduleDetail CSV |
| the file name | `NN_Topic_Name.deck.html`, from the session row that names it |
| the approved outline | from `references/material/tasks/propose_outline.md` |

## Produces

`NN_Topic_Name.deck.html` in `materials_dir`.

## Steps

1. **Outline first.** Without an approved outline for this deck, stop and run
   `references/material/tasks/propose_outline.md`; write nothing until the user
   approves it. The approved outline fixes the slides, their layouts and their
   order. If `materials_dir/_theme/` does not exist, run
   `FSA material init --dir "<materials_dir>"`.
2. Start from `references/material/templates/deck.html`. Pick each slide's layout
   from `references/material/layouts.md`; a slot outside its layout, or text past
   its limit, has nowhere to go in the exported `.pptx`.
3. Shape the lesson before writing slides: two to four sections, each one idea
   the objectives need. Budget the slides against the minutes, at roughly two to
   four minutes a slide; `verify` warns outside 1.5–6 (`MAT-S09`).
4. Keep the template's order: cover, table of contents (optional, left empty),
   Lesson Objectives, then each section opened by its section cover, then Lesson
   Summary and the closing slide (`MAT-S01`). `closing` is the template's own
   photograph; `closing-gradient` and `closing-illustration` are its other two.
5. Every objectives item and every summary item carries `data-objective`; the
   summary closes each objective the slide opened (`MAT-S04`, `MAT-S05`).
6. One idea per slide. The title states the point ("Prefer a surrogate key"),
   not the topic ("Keys"). Type sizes are the template's; a title too long for
   its slot shrinks in steps, the same in the browser, the `.pptx` and the
   `.pdf`. Keep titles short enough to stay near the template's size: `MAT-S10`
   reports one shrunk below 70%, and `MAT-S08` one that does not fit at all.
   At most six items, two levels deep; at most twelve lines of code, each short
   enough for its column. Use `two-content` with `pre class="wrong"`/`"right"` for a
   common mistake, and the box, column and row layouts for three or four parallel
   ideas rather than a long list.
7. End every section with a check slide: `data-role="check"`, a question the
   room answers from what they just saw, the answer in `<details>` (`MAT-S07`).
8. Write speaker notes on every objectives and content slide, in the trainer's
   words: what to say, what to ask, what to point at. They become the `.pptx`
   notes and, later, a recording script (`MAT-S06`).
9. Draw diagrams by `references/material/conventions.md` § Diagrams.

## Done when

`FSA material verify "<materials_dir>"` reports no errors for the deck, and it
reads correctly in a browser (arrow keys; N for notes, O for the overview).

## Hands off to

`references/material/tasks/write_lecture.md` for the same session, then
`references/material/tasks/export.md`.
