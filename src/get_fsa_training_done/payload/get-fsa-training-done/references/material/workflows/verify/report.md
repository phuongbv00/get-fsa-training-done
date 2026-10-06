# Workflow — read a verification report

```bash
FSA material verify "<folder>"
FSA material verify "<file>" --type lab
FSA material verify "<folder>" --json
```

Prefer a folder. The index rules — unique, contiguous, `00` and `99` reserved —
only mean anything across a whole module.

## Reading it

Every finding names its rule; `references/material/structure.md` explains each one and
why it exists.

**Errors** are structural: the document will not render, link or list correctly.
**Warnings** are judgement: a short knowledge check, an unusual fence language,
Vietnamese in a file not marked as a translation. `--strict` promotes them.

## Existing material will fail, and that is the point

The corpus this template describes has three generations in it. Older notes
predate the conventions and will report real findings — a mid-file `#` heading,
untagged fences, no knowledge check. That is a true description of those files,
not a false alarm.

When checking material you did not write, say plainly which findings are
pre-existing rather than caused by the change at hand.

## Common findings

| Rule | Usually means |
|---|---|
| `MAT-D04` | a `#` used mid-file as a part divider; make it `##` |
| `MAT-D06` | the note opens with content and never said what it is for |
| `MAT-D10` | a bare ``` fence; tag it, `text` if it is not code |
| `MAT-D12`/`D13` | a note or a heading was renamed and a link still points at the old one |
| `MAT-D16` | Vietnamese in a file not ending `_vn`; a translation is a separate file |
