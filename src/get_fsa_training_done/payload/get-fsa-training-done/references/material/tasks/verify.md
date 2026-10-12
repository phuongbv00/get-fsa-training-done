# Task — Verify material

Check documents against the shape their names claim.

## Inputs

| Input | Notes |
|---|---|
| paths | prefer the whole folder; the index rules only mean anything across a module |

## Produces

PASS or FAIL, with findings that name their rule.

## Steps

```bash
FSA material verify "<materials_dir>"
FSA material verify "<file>" --type lab
FSA material verify "<materials_dir>" --export
FSA material verify "<materials_dir>" --json
```

1. Every finding names its rule; `references/material/structure.md` explains
   each. **Errors** are structural; **warnings** are judgement, and `--strict`
   promotes them.
2. Material is HTML; `verify` reads only `.html` files. When checking files you
   did not write, say which findings were already there.
3. Common findings: `MAT-S10` (a title too long for the template's type size),
   `MAT-S01` (a deck out of the template's order), `MAT-S06`
   (a slide with no speaker notes), `MAT-S07` (a section with no check slide),
   `MAT-D22` (inline styling), `MAT-D25` (a question with no answer), `MAT-D28`
   (a concept with nothing to try), `MAT-D12`/`D13` (a renamed file or id still
   linked), `MAT-D16` (Vietnamese outside a `_vn` file), `MAT-D19`/`D20` (a
   diagram's cardinality or colours).
4. `--export` adds what a `.pptx` or `.pdf` cannot carry (`MAT-X*`).

## Done when

No errors, and every warning is fixed or named as deliberate.

## Hands off to

The report back in `references/material/overview.md`.
