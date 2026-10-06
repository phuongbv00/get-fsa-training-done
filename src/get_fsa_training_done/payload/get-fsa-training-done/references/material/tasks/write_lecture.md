# Task — Write a lecture note

A unit of reading that serves one session of the plan.

## Inputs

| Input | Notes |
|---|---|
| `materials_dir` | the module's folder; never assumed |
| `schedule` | the topic's ScheduleDetail CSV |
| the file name | `NN_Topic_Name.md`, from the session row that names it |

## Produces

`NN_Topic_Name.md` in `materials_dir`.

## Steps

1. Find the session row that names this file: its objective codes, its minutes,
   and its one line on what happens. Write to *that*: a note covering more than
   its session is a note the session cannot deliver. Echo the absolute path and
   the session it serves, and wait for a go-ahead.
2. Take the shape from `references/material/structure.md` (the **unit**
   template), the skeleton `references/material/templates/lecture_note.md`, and
   `references/material/conventions.md`. Not negotiable, because `verify` checks
   them: one `#` title on line 1 and no front matter; `## 1. Objectives` opening
   `After this unit, learners can:`; sections numbered `1..n`; a knowledge
   check, then somewhere to go next; a language tag on every fence.
3. Write it to the trainee: explain, then show, in the module's running domain.
   Pair the wrong and right forms where a mistake is common. Cite the session's
   objective codes in the objectives.
4. Draw diagrams by `references/material/conventions.md` § Diagrams.

## Done when

`FSA material verify "<materials_dir>"` reports no errors for the note — run it
over the folder, since the index rules only make sense across a module.

## Hands off to

`references/material/tasks/review_for_trainee.md` before publishing.
