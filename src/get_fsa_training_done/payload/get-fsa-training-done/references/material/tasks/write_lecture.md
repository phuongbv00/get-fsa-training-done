# Task — Write a lecture note

The reading behind a lesson: what the slides compress, explained in full, with
practice after each idea. It serves one session of the plan.

## Inputs

| Input | Notes |
|---|---|
| `materials_dir` | the module's folder; never assumed |
| `schedule` | the topic's ScheduleDetail CSV |
| the file name | `NN_Topic_Name.html`, from the session row that names it |
| the deck | `NN_Topic_Name.deck.html`, when the session has one |
| the approved outline | from `references/material/tasks/propose_outline.md` |

## Produces

`NN_Topic_Name.html` in `materials_dir`.

## Steps

1. **Outline first.** Without an approved outline for this note, stop and run
   `references/material/tasks/propose_outline.md`; write nothing until the user
   approves it. Write to the session the outline cites: a note covering more
   than its session is a note the session cannot deliver.
2. Start from `references/material/templates/lecture_note.html`; the parts and
   their order are in `references/material/structure.md` and `verify` checks
   them. When the session has a deck, follow its sections: one `concept` part
   per section, so a trainee can move between the two.
3. **Why This Matters** comes before any concept: the problem the lesson solves,
   in the module's running domain, in a paragraph.
4. Each concept part: the idea in prose first, then the example (`MAT-D27`),
   then a `try-it` on exactly that idea, its answer in `<details>` (`MAT-D28`).
   Pair the wrong and right forms where a mistake is common.
5. The worked example states the problem and the approach before the code, and
   says how to read the result.
6. The summary has one item per objective, and the knowledge check at least five
   questions; every question carries `data-objective` and its answer, and every
   objective is asked about (`MAT-D25`, `MAT-D26`).
7. Draw diagrams by `references/material/conventions.md` § Diagrams.

## Done when

`FSA material verify "<materials_dir>"` reports no errors for the note — run it
over the folder, since the index rules only make sense across a module.

## Hands off to

`references/material/tasks/review_for_trainee.md` before publishing.
