# Workflow — write a lecture note

**Produces:** `NN_Topic_Name.md` in the module's materials folder.

## 1. Find out what the note is for

A note serves a session. Ask for the topic's `<TOPIC>_ScheduleDetail.csv` and
find the row that names this file: it gives the session, the objective codes,
the minutes, and one line saying what happens.

Write to *that*. A note covering more than its session is a note the session
cannot deliver.

## 2. Take the shape from `references/structure.md`

Use the **unit** template. `references/templates/lecture_note.md` is the
skeleton; `references/conventions.md` covers register, callouts and code.

The parts that are not negotiable, because `verify` checks them:

- one `#` title on line 1, no front matter
- `## 1. Objectives` opening `After this unit, learners can:`
- numbered sections running `1..n`
- a knowledge check, then somewhere to go next
- a language tag on every fence

## 3. Write it

Explain then show. Keep one worked domain across the module. Where a mistake is
common, pair the wrong and right forms rather than describing the difference.

Cite the objective codes from the session row in the objectives section.

## 4. Check it

```bash
FSA material verify "<folder>"
```

Run it over the **folder**, not the single file: the index rules only make sense
across a module.
