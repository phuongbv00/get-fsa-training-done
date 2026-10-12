# Writing conventions

`references/material/structure.md` says what sections a document must have. This says how
to write inside them, and every rule here comes from the corpus rather than from
taste.

## Who is reading

The trainee, working through the module alone. Address them directly — "you
run", "your query returns" — and write what they need to understand and do.
Never write the session as the instructor runs it ("ask the class", "spend ten
minutes on"): material that reads like trainer notes is published to the wrong
reader. Everything in `references/common/style.md` applies.

## Slides

A slide is read from across a room in seconds; it carries the point, and the
speaker notes carry the explanation.

- **One idea per slide**, and a title that states it: "Prefer a surrogate key",
  not "Keys".
- **Parallel ideas go side by side.** Three or four related ideas belong in the
  box, column or row layouts, not in a long list.
- **A check slide ends every section**: a question answered from what was just
  shown, the answer folded into `<details>` and revealed after the room commits.
- **Speaker notes are the lesson in the trainer's voice**: what to say, what to
  ask, what to point at. Write them so another trainer could give the session.
- **The note follows the deck.** One concept part per section, in the same
  order and the same words, so a trainee can move between them.

## Register

Explain, then show. A concept section states the idea in prose, then a short
self-contained snippet. Snippets are named and exported so a learner can paste
one somewhere and have it run.

Comments in code carry the teaching point — `// theme is correctly absent here`
— never a restatement of the line above.

## Practice

Every concept in a note ends with a `<div class="try-it">`: a small exercise on
exactly that idea, its answer in `<details>`. Every knowledge-check question has
its answer too. A trainee working alone learns by trying and checking; a note
without answers only lets them guess.

## Callouts

An `<aside class="callout note|tip|warning">`, with a bolded lead word and a
full stop:

```html
<aside class="callout tip"><p><strong>Tip.</strong> …</p></aside>
```

## Showing a mistake

Pair the wrong and the right form as `<pre class="wrong">` and
`<pre class="right">`; the theme labels them. A learner who has hit the mistake finds it by searching for the
symptom, so a `Common Problems` sub-heading should *be* the symptom or the
literal error message.

## Code

Always `<pre><code class="language-…">`. Use `language-text` for the blocks that
are not code at all — console output, directory trees, error text. That
convention is what makes the tag meaningful for the blocks that *are* code.

## Diagrams

Draw them in Mermaid, never as ASCII art, inside a figure —
`<figure><pre class="mermaid">…</pre><figcaption>…</figcaption></figure>` — and
pick the diagram type for what it shows:

- **A flow between parties** — a request and its response, a client and a
  server, you and Git — is a `sequenceDiagram`.
- **Structure** is a `flowchart` or a `classDiagram`; **history** is a
  `gitGraph`.
- **An ER diagram** labels every relationship with its cardinality in words,
  first: `CUSTOMER ||--o{ ORDER : "1-n places"`. The crow's-foot marks alone
  are the notation the trainee is still learning (`MAT-D19`).
- **Colours come from the theme.** No `style`, `classDef` or `themeVariables`
  colours: the material is read in light and dark mode, and a fixed colour is
  unreadable in one of them (`MAT-D20`). Emphasis is a label or a subgraph.
- **Changing a diagram's colours changes only its colours.** Keep its nodes,
  edges and layout exactly as they were.
- An entity is a *type*: a table's rows are its instances. Say which one a
  diagram shows.
- **Before exporting**, add a PNG of the rendered diagram to the same figure
  (`<img src="…png" alt="…">`). PowerPoint and the PDF writer cannot run
  Mermaid; the browser shows the image when there is one (`MAT-X01`).

## A running domain

Keep one worked domain across a module and say what it is in the handbook. The
examples then compose instead of resetting every unit.

## Objective codes

A note serves the objective codes its session claims in the plan. Put each on
its objective as `data-objective`, and on the summary item and the questions that
close it; `coverage` compares them against both the plan and the syllabus.

## Language

A document is written in the language its `<html lang>` declares: English
(`en`) unless the module is written in Vietnamese (`vi`). Declare it on every
file of the module, and keep one language per module.

The theme, the viewer and the exporters follow that declaration for every word
they write on your behalf — a slide's default title (*Mục tiêu bài học*,
*Tóm tắt bài học*), the *Thử ngay* and *Kết quả mong đợi* labels, *Sai* /
*Đúng*, a PDF's *Buổi 3 · 90 phút* line, the appendix's map heading. Write your
own labels — a check slide's `<summary>`, a hint's — in the same language
(*Đáp án*, *Gợi ý*). Open the objectives in it too: *After this unit, learners
can:* or *Sau bài học này, học viên có thể:*.

Code, identifiers, commands and error messages stay as they are, in English;
technical terms may too, but keep one term for one thing across the module.

A **translation** of an English original is a separate file whose stem ends
`_vn` and which declares `lang="vi"` — never a rewrite of the original. Everything
else links to the original, so replacing it in place breaks those links and
leaves half the module in one language. Write it with
`references/common/tasks/translate_vn.md`.

## Group labs

A lab run by groups ships a worksheet beside it, `<subject>_lab_NN_worksheet.html`:
the tables and headings each group fills in, drawn in advance, so session time
goes into the work rather than into layout. The lab guide names it in
`## Before you start`.

## What belongs elsewhere

| Content | Feature |
|---|---|
| quiz questions, assignment briefs, exam papers, rubrics, grading | the assessment feature |
| session plans, syllabi, schedules, the module's shape | the program feature |

A lab guide is the guided middle: shorter than an assignment, step-numbered, and
checkable by the learner. If it has marks and a rubric it is an assignment, and
it belongs to the assessment feature.
