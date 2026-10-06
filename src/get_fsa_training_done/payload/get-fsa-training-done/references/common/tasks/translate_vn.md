# Task — Translate to Vietnamese

Produce the `_vn` sibling of a finished English artifact: a brief, an answer
template, a learner template, a master question CSV, a lecture note or a lab.

## Inputs

| Input | Notes |
|---|---|
| the English file | finished and verified first — a translation of a draft doubles every later edit |
| `output_dir` | the folder the English file is in, unless the user names another |

## Produces

`<stem>_vn.<ext>` beside the original, named as `references/common/language_vn.md`
lists. For a master CSV, also its `_vn` import file, emitted, never translated by
hand.

## Steps

1. Read `references/common/language_vn.md` and `references/common/style.md`.
2. Translate prose only. Keep every heading, banner line, `**Qn.**` marker, code
   block, file name and technical term exactly as in the original.
3. For a master CSV, translate `Question` and `Answer 1-4` only, then emit the
   import file from the `_vn` master with the same `FSA assessment emit` command
   the original used.
4. For a brief, render it: `FSA assessment render "<stem>_vn.md" --lang vi`.
5. Run the same `verify` the original passed, pointing at the `_vn` files. A
   written exam's `_vn` brief is checked against the English rubric, which is
   never translated.

## Done when

The `_vn` file passes the same `verify` as the original, its PDF (for a brief)
fits the same page budget, and a diff of headings and code blocks against the
original is empty.

## Hands off to

Nothing. If the English file changes later, regenerate the translation from it
rather than editing both.
