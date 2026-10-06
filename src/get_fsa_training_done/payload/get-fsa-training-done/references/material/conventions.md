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

## Register

Explain, then show. A concept section states the idea in prose, then a short
self-contained snippet. Snippets are named and exported so a learner can paste
one somewhere and have it run.

Comments in code carry the teaching point — `// theme is correctly absent here`
— never a restatement of the line above.

## Callouts

Blockquotes, with a bolded lead word and a full stop:

```text
> **Note.** …
> **Tip.** …
> **Real-world use.** …
```

## Showing a mistake

Pair the wrong and the right form and label them in comments — `// Wrong`,
`// Right`. A learner who has hit the mistake finds it by searching for the
symptom, so a `Common Problems` sub-heading should *be* the symptom or the
literal error message.

## Fences

Always tagged. Use `text` for the blocks that are not code at all — console
output, directory trees, error text. That convention is what makes the tag
meaningful for the blocks that *are* code.

## Diagrams

Draw them in `mermaid`, never as ASCII art, and pick the diagram type for what
it shows:

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

## A running domain

Keep one worked domain across a module and say what it is in the handbook. The
examples then compose instead of resetting every unit.

## Objective codes

A note serves the objective codes its session claims in the plan. Cite them in
the objectives section; `coverage` compares them against both the plan and the
syllabus.

## Language

English. A translation is a **separate file** whose stem ends `_vn`, never a
rewrite of the original — everything else links to the original, so replacing it
in place breaks those links and leaves half the module in one language. Write it
with `references/common/tasks/translate_vn.md`.

## Group labs

A lab run by groups ships a worksheet beside it, `<subject>_lab_NN_worksheet.md`:
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
