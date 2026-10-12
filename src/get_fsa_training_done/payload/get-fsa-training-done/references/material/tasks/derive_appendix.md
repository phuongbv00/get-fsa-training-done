# Task — Write or refresh the appendix

`99_Appendix.html` maps the syllabus onto the lecture note's topics, so a trainee
revising can find where each outline item is covered.

## Inputs

| Input | Notes |
|---|---|
| `syllabus` | the topic's syllabus |
| `materials_dir` | the module folder holding the lecture note it maps |

## Produces

`99_Appendix.html`, from `references/material/templates/appendix.html`. Index
`99` is reserved for it.

## Steps

1. **Outline first** when the appendix does not exist yet: its outline — the
   items the map will link and the references — goes through
   `references/material/tasks/propose_outline.md`. Refreshing the map of an
   existing appendix with `--check`/`--write` needs no outline.
2. Derive the syllabus map; never type it — a renamed heading breaks deep links
   silently:

   ```bash
   FSA material derive appendix --syllabus "<TOPIC>_Syllabus.md" \
     --dir "<materials_dir>" --appendix "99_Appendix.html" --write
   ```

3. Read the result. It matches on wording, so an item linked to the wrong topic,
   or left unlinked, means the outline and the note name the same thing
   differently.
4. Write the references part by hand: the module's primary sources.

## Done when

`FSA material derive appendix ... --check` exits 0 and `verify` passes.

## Hands off to

Nothing. Re-run `--check` whenever the note or the outline changes.
