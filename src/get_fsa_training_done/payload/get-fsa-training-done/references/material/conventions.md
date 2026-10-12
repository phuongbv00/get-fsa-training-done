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
- **Show, then say.** Every section carries an illustration (`MAT-S12`): a
  diagram, a screenshot, a table of real rows, code beside its output. Words
  describe; the picture is what a trainee remembers. Reach for the picture
  layouts — `content-picture` for a point beside what it describes,
  `title-only` for a diagram that needs the whole slide — before a list.
- **Fill the slide** (`MAT-S11`). Three bullets on a white layout leave its
  lower half blank. Add what they describe, choose a layout with fewer, larger
  parts, or merge the slide with the next; never pad with more bullets.
- **Parallel ideas go side by side.** Three or four related ideas belong in the
  box, column or row layouts, not in a long list.
- **A check slide ends every section**: a question answered from what was just
  shown, the answer folded into `<details>` and revealed after the room commits.
  Give it something to look at: the rows, the code or the picture the question
  is about, not the question alone.
- **Speaker notes are the lesson in the trainer's voice**: what to say, what to
  ask, what to point at. Write them so another trainer could give the session.
- **The note follows the decks.** The lecture note has one topic per lesson,
  in deck order and in the same words, so a trainee can move between them.

## Register

Explain, then show. A point states the idea in prose, then a short
self-contained snippet. Snippets are named and exported so a learner can paste
one somewhere and have it run.

Comments in code carry the teaching point — `// theme is correctly absent here`
— never a restatement of the line above.

## Practice and revision

A trainee practises in the session — a check slide after every section — and in
the lab. The lecture note is for revising: condensed theory, then review
questions of the kind a theory exam or an interviewer asks, each with a model
answer in `<details>`. A trainee revising alone learns by answering and
checking; questions without answers only let them guess.

## Callouts

An `<aside class="callout note|tip|warning">`, with a bolded lead word and a
full stop:

```html
<aside class="callout tip"><p><strong>Tip.</strong> …</p></aside>
```

## Showing a mistake

Pair the wrong and the right form as `<pre class="wrong">` and
`<pre class="right">`; the theme labels them. A learner who has hit the mistake finds it by searching for the
symptom, so a lab's hint should name the symptom or the literal error message,
and a lecture note's `Common Misconceptions` sub-heading the wrong belief as a
trainee would say it.

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
- **Before exporting**, add an image of the diagram to the same figure
  (`<img src="…" alt="…">`). PowerPoint and the PDF writer cannot run
  Mermaid; the browser shows the image when there is one (`MAT-X01`).

### Drawing an illustration as SVG

When no screenshot or photograph shows the point, draw it: an SVG file under
`img/`, linked from an `<img>` like any picture. The browser shows it as it is,
and `export` draws it to a PNG for the `.pptx` and the `.pdf` — no tool to run.

- **The theme's colours**: brand blue `#034ea1`, green `#50b748`, ink
  `#1f2328`, muted text `#5b6370`, surface `#f2f5fa`, rules `#d3dbe8`. Give the
  drawing its own background (a `#f2f5fa` or white rectangle), so it reads on a
  dark page too.
- **Type**: `font-family="sans-serif"` on the root, or `monospace` for code;
  the export draws them in the module's own fonts, so Vietnamese keeps its
  diacritics. No text below 12pt on the slide (`MAT-S13`): at a 400-wide
  `viewBox` in `content-picture`, `font-size` 18 or more.
- **Shapes only**: rectangles, circles, lines, paths, polygons, text and
  groups. No `<marker>` (draw an arrowhead as a small `<polygon>`), filters,
  masks, patterns, text paths or HTML inside — the export cannot draw them and
  they vanish from the file handed out (`MAT-X04`).
- **Draw at the slot's shape** (`MAT-S13`): `references/material/layouts.md`
  gives every slot's box. `content-picture`'s picture is near square (285 × 298
  pt — a `viewBox` of 400 × 420); `title-only`'s canvas is wide (655 × 299 pt —
  about 880 × 400). A drawing of another shape is shrunk to fit, leaving the
  slot part empty and its text too small.
- One idea per drawing, labelled in the lesson's words; at most about five
  boxes, and detail left to the speaker notes.
- Every `<img>` says what it shows in `alt` (`MAT-D24`).

## A running domain

Keep one worked domain across a module and say what it is in the lecture note's
Running Example. The
examples then compose instead of resetting every unit.

## Objective codes

A deck or a lab serves the objective codes its session claims in the plan; the
lecture note serves those of every session that names it. Put each on
its objective as `data-objective`, and on the summary item and the questions that
close it; `coverage` compares them against both the plan and the syllabus.

## Language

A document is written in the language its `<html lang>` declares: English
(`en`) unless the module is written in Vietnamese (`vi`). Declare it on every
file of the module, and keep one language per module.

The theme, the viewer and the exporters follow that declaration for every word
they write on your behalf — a slide's default title (*Mục tiêu bài học*,
*Tóm tắt bài học*), the *Thử ngay* and *Kết quả mong đợi* labels, *Sai* /
*Đúng*, a PDF's *Buổi 3 · 90 phút* line, the syllabus map's heading. Write your
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
