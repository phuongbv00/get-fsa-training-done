# Task — Write or refresh the appendix

`99_Appendix.md` maps the syllabus onto the notes, so a trainee revising can find
where each outline item was covered.

## Inputs

| Input | Notes |
|---|---|
| `syllabus` | the topic's syllabus |
| `materials_dir` | the notes it maps |

## Produces

`99_Appendix.md`. Index `99` is reserved for it.

## Steps

1. Derive the syllabus map; never type it — a renamed heading breaks deep links
   silently:

   ```bash
   FSA material derive appendix --syllabus "<TOPIC>_Syllabus.md" \
     --dir "<materials_dir>" --appendix "99_Appendix.md" --write
   ```

2. Read the result. It matches on wording, so an item linked to the wrong note,
   or left unlinked, means the outline and the notes name the same thing
   differently.
3. Write by hand: Key topics (what to revise first), Reference List (primary
   sources), Glossary.

## Done when

`FSA material derive appendix ... --check` exits 0 and `verify` passes.

## Hands off to

Nothing. Re-run `--check` whenever a note or the outline changes.
