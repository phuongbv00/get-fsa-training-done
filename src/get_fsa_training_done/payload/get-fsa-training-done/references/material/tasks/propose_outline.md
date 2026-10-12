# Task — Propose an outline and have it approved

Every document this feature writes starts as an outline the user approves. A
deck rebuilt after review costs an hour; an outline corrected before writing
costs a minute — and it is the only point where the user can change the shape of
a lesson rather than its wording.

**No document file is created or overwritten until its outline has an explicit
go-ahead.** Not as a draft, not "to show what it would look like".

## Inputs

| Input | Notes |
|---|---|
| the documents | each file to be written, by name, with the kind its name claims |
| `schedule` | the session row naming each file: objective codes, minutes, `Content` |
| `materials_dir` | where they will be written; never assumed |
| what exists | for a rewrite, the current file |

## Produces

An outline per document, echoed in the conversation, and the user's explicit
approval of each. No files.

## Steps

1. Read each document's session row. An outline that does not cite the
   session's objective codes and minutes is a guess at the wrong lesson.
2. Write the outline in the shape for its kind, below. Plain lists, no HTML; say
   what each part *teaches*, not just its heading.
3. Open each outline with one line: the absolute path, the kind, the session it
   serves, its objective codes and its minutes.
4. Show every outline the request covers in one message, so the user can see how
   a lesson's deck and lab, and the module's note, divide the work — then **stop and ask**:
   approve, change, or drop each. Silence, "looks fine probably" or a question
   back is not approval.
5. Apply the changes and show the revised outline again. Repeat until each
   document has its own explicit go-ahead; an approval of one document is not an
   approval of the next.
6. The approved outline is the contract for the writing task: write what it
   lists, in its order. A part the writing shows must change goes back to the
   user as a revised outline, not into the file unannounced.

### Outline shapes

**Deck** (`NN_Topic_Name.deck.html`)

- The slide budget: minutes ÷ slides, inside the 1.5–6 minutes a slide `verify`
  allows.
- Per slide, in order: number · `data-layout` · the title as a statement, within
  its layout's character budget in `references/material/layouts.md` · one
  line on what it says · **the illustration it shows** (a diagram to draw, a
  screenshot, a table of rows, code) or "none" · for a check slide, the
  question and its answer. Every section has at least one illustration.
- Cover, toc, objectives (each with its code), then per section its cover and
  slides, then the summary (each item with the code it closes) and the closing
  layout.

**Lecture note** (`<subject>_lecture_note.html`, one per module)

- The module's objectives, each with its code — the union of every session that
  names the note.
- The module map, a row per lesson with the files it will link; the study
  routine; the environment with versions; the running domain.
- Per topic, one per lesson in deck order: its id, the deck it condenses, and
  the points it holds — definitions, rules, the comparison tables.
- The misconceptions, each as a trainee would say it; the review questions,
  each with its code and a one-line model answer, at least two per topic; the
  glossary terms; which outline items the derived syllabus map will link where;
  further reading.

**Lab guide** (`<subject>_lab_NN.html`)

- The objectives with codes, and what must already work.
- Per step: the action, what the trainee should see, minutes, and any hint.
  The minutes add up to no more than the session's.
- The acceptance checklist, the stretch, and whether a worksheet is needed.

**Worksheet** — the outputs the lab asks for, each with the table it needs.



## Done when

The user has given an explicit go-ahead on the echoed outline of every document
about to be written.

## Hands off to

The writing task for each document: `references/material/tasks/write_deck.md`,
`references/material/tasks/write_lecture.md`, `references/material/tasks/write_lab.md`
or `references/material/tasks/write_worksheet.md`.
