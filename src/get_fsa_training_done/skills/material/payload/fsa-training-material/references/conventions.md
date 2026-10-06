# Writing conventions

`references/structure.md` says what sections a document must have. This says how
to write inside them, and every rule here comes from the corpus rather than from
taste.

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

Always tagged. Use `text` for the blocks that are not code at all — ASCII
diagrams, console output, directory trees, error text. That convention is what
makes the tag meaningful for the blocks that *are* code.

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
in place breaks those links and leaves half the module in one language.

## What belongs elsewhere

| Content | Skill |
|---|---|
| quiz questions, assignment briefs, exam papers, rubrics, grading | `fsa-training-assessment` |
| session plans, syllabi, schedules, the module's shape | `fsa-training-program` |

A lab guide is the guided middle: shorter than an assignment, step-numbered, and
checkable by the learner. If it has marks and a rubric it is an assignment, and
it belongs to the assessment skill.
