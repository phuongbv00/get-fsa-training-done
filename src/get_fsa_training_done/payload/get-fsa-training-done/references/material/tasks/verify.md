# Task — Verify material

Check documents against the template their names claim.

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
FSA material verify "<materials_dir>" --json
```

1. Every finding names its rule; `references/material/structure.md` explains
   each. **Errors** are structural; **warnings** are judgement, and `--strict`
   promotes them.
2. Older material predates the conventions and fails on purpose. When checking
   files you did not write, say which findings were already there.
3. Common findings: `MAT-D04` (a mid-file `#`), `MAT-D06` (no objectives),
   `MAT-D10` (an untagged fence), `MAT-D12`/`D13` (a renamed note or heading
   still linked), `MAT-D16` (Vietnamese outside a `_vn` file), `MAT-D19`/`D20`
   (a diagram's cardinality or colours).

## Done when

No errors, and every warning is fixed or named as deliberate.

## Hands off to

The report back in `references/material/overview.md`.
