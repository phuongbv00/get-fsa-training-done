# Task — Write the module handbook

`00_Study_Guide_Handbook.html`: the first thing a trainee opens, and the only
place that describes the module as a whole.

## Inputs

| Input | Notes |
|---|---|
| `materials_dir` | the module's folder |
| `schedule` | the topic's ScheduleDetail CSV: the lessons, in order |
| the approved outline | from `references/material/tasks/propose_outline.md` |

## Produces

`00_Study_Guide_Handbook.html`. Index `00` is reserved for it.

## Steps

1. **Outline first.** Without an approved outline for the handbook, stop and run
   `references/material/tasks/propose_outline.md`; write nothing until the user
   approves it. Then run `FSA material init --dir "<materials_dir>"` if
   `_theme/` is missing, and start from `references/material/templates/handbook.html`.
2. **Module Map**: one row per lesson, in order, linking its deck, its topic in
   the lecture note (`<subject>_lecture_note.html#<topic-id>`) and its lab. A file not written yet is listed without a link and written next.
3. **How to Study This Module**: a routine per lesson — before, during and
   after the session — that uses what each kind of material is for: slides in
   the room, the lesson's topic in the lecture note after, then the lab; and
   before the theory exam or an interview, the note's summary and review questions.
4. **Environment Setup**, pinned to versions, with a command that proves each
   piece works. Say how to tell when something read elsewhere is out of date.
5. **The Running Example**: the one domain the lessons share, so every example
   composes instead of resetting.

## Done when

`FSA material verify "<materials_dir>"` reports no errors for it.

## Hands off to

`references/material/tasks/write_deck.md` for the first lesson.
