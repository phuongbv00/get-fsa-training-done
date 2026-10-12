# Task — Derive the syllabus map

The lecture note's **Full Syllabus Map** maps each item of the syllabus outline
to the topic that covers it, so a trainee revising can tick off the syllabus and
find where each item is. It is derived, never typed: a renamed heading breaks a
typed link silently.

## Inputs

| Input | Notes |
|---|---|
| `syllabus` | the topic's syllabus; its § 7 Topic Outline is mapped |
| the note | `<subject>_lecture_note.html`; its `syllabus-map` part may be empty, stale or missing |

## Produces

The note's `syllabus-map` part, rewritten in place — or added before Further
Reading when the note has none. Nothing else in the note changes.

## Steps

1. Derive the map into the note:

   ```bash
   FSA material derive syllabus-map --syllabus "<TOPIC>_Syllabus.md" \
     --note "<materials_dir>/<subject>_lecture_note.html" --write
   ```

   It writes in the note's language (`<html lang>`), and needs no outline: it
   only refreshes a part the note's approved outline already has.
2. Read the result. It matches on wording, so an item linked to the wrong topic,
   or left unlinked, means the outline and the note name the same thing
   differently — rename the topic's heading, not the map.

## Done when

`FSA material derive syllabus-map ... --check` exits 0 and `verify` passes.

## Hands off to

Nothing. Re-run `--check` whenever a topic or the outline changes.
