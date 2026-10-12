# Task — Review material for the trainee

Read finished material the way a trainee will, before it is published.

## Inputs

| Input | Notes |
|---|---|
| the documents | decks, the lecture note, labs, and the starter code they link to |
| the level | from the programme: `CPL`, `FR`, `UP_SKILL` or `RE_SKILL` |

## Produces

A list of changes, then the changes made.

## Steps

1. **Work through it as the trainee.** Read only this lesson and the ones
   before it, at the programme's level. Answer every check slide and every
   review question before opening its answer, and do every lab step in order. Note each place you
   stalled: a term used before it was defined, a step that assumed one not
   written, an exercise its section did not prepare you for. Those are the
   findings that matter most.
2. **Slides and note agree.** Each topic of the lecture note condenses its
   lesson's deck, in the same order and the same words for the same things, and
   a trainee who knows the note can answer every review question.
3. **Who it speaks to.** On slides and in notes, write to the trainee. Speaker
   notes are the one place written to the trainer. Rewrite anything else
   addressed to the instructor ("ask the class to...") as what the trainee does.
4. **Correctness.** A claim about a tool's behaviour must be one you can stand
   behind; where it can be shown, show it — run the snippet through
   `references/common/tasks/run_in_sandbox.md` rather than asserting what a
   compiler or a database does.
5. **Diagrams** follow `references/material/conventions.md` § Diagrams.
6. **Plain words** per `references/common/style.md`.
7. Leave what was not asked about alone: a review of the content does not
   restyle code that was not in scope.

## Done when

The changes are made and `FSA material verify` still passes.

## Hands off to

`references/material/tasks/export.md`.
