# Workflow — write a module appendix

**Produces:** `99_Appendix.md`.

Index `99` is reserved for it. It maps the syllabus onto the notes, so a learner
revising can find where each outline item was covered.

## The syllabus map is derived

Do not type it. It links into specific sections of specific notes, and those are
the only deep links in a module — a renamed heading breaks them and nothing else
reports it.

```bash
FSA material derive appendix \
  --syllabus "<TOPIC>_Syllabus.md" --dir "<folder>" \
  --appendix "99_Appendix.md" --write
```

That matches each topic-outline item to the note whose headings best cover it
and writes `- [ ] <item> → [NN](NN_File.md#anchor)`. It is a match on wording,
so **read the result**: an item it linked to the wrong note, or left unlinked,
is telling you either the outline or the notes use different words for the same
thing.

## Write the rest by hand

- **Key topics** — what to revise first.
- **Reference List** — primary sources, not blog posts.
- **Glossary** — the terms the module leaves undefined.

## Keep it current

```bash
FSA material derive appendix --syllabus … --dir … --appendix … --check
```

Exit code 1 means a note was renamed, a heading moved, or the outline changed
since the map was written.
