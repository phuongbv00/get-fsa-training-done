# Task — Emit the platform import files

Derive the files a quiz platform imports from the master question CSV. They are
generated, never written by hand, so they cannot drift from the master.

## Inputs

| Input | Notes |
|---|---|
| `<stem>.csv` | the verified master |
| platform | Blooket for a quiz, Coderbyte for a multiple-choice theory exam |

## Produces

`<stem>_blooket.csv` or `<stem>_coderbyte.json`. Both encode the answers: hand
them to the platform, not to trainees, and not before the session.

## Steps

```bash
FSA assessment emit blooket   --master "<stem>.csv" -o "<stem>_blooket.csv"
FSA assessment emit coderbyte --master "<stem>.csv" -o "<stem>_coderbyte.json"
```

- Blooket needs a title row for delimiter detection and caps a timer at 300s;
  the emitter handles both.
- Coderbyte marks answers by position and **index 0 is always correct**,
  whether or not it is in `correctAnswers`: `["2", "3"]` over four answers means
  0, 2 and 3 are correct. The emitter therefore always puts a correct option
  first. A hand-written file that leaves a wrong option at index 0 imports
  without complaint and marks that wrong option correct.
- A Vietnamese set is emitted from its own `_vn` master: `<stem>_vn_blooket.csv`.

## Done when

`FSA assessment verify` passes with the import file given alongside the master
(`--blooket` or `--coderbyte`).

## Hands off to

`references/assessment/tasks/design/verify.md`.
