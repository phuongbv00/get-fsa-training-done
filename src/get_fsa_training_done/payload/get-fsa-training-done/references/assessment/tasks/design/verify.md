# Task — Verify the assessment

Run the structural checks, then the verifier agent. Structure is the CLI's
job; whether the content is any good is the agent's.

## Inputs

| Input | Notes |
|---|---|
| the generated files | as the type's workflow lists them |
| `level` | `CPL`, `FR`, or a banded level as `UP_SKILL:mid` |

## Produces

A PASS or FAIL with its findings, and the verifier agent's verdict.

## Steps

1. Run the check for the form being verified:

   | Form | Command |
   |---|---|
   | multiple-choice quiz | `FSA assessment verify --type quiz --master <stem>.csv --blooket <stem>_blooket.csv --level <L> --expect-count N` |
   | multiple-choice theory exam | `FSA assessment verify --type theory_exam --master <stem>.csv --coderbyte <stem>_coderbyte.json --level <L>` |
   | written quiz | `FSA assessment verify --type quiz --brief <stem>.md --rubric <stem>_rubric.md --pdf <stem>.pdf --level <L>` |
   | written theory exam | `FSA assessment verify --type theory_exam --brief <stem>.md --rubric <stem>_rubric.md --answer-template <stem>_answer_template.md --pdf <stem>.pdf --level <L>` |
   | assignment, practice exam | `FSA assessment verify --type <type> --brief <stem>.md --rubric <stem>_rubric.md --pdf <stem>.pdf --level <L>` (add `--answer-template` for a worksheet) |

   The files given decide the form: `--master` for multiple choice, `--brief`
   and `--rubric` for written. Level drift is a warning, never an error; pass
   `--time-map` only when the confirmed map differs from the level's.
2. Fix every error and re-run. A warning is either fixed or named as deliberate
   in the report.
3. Run the type's verifier prompt from `references/assessment/verifiers/` with
   the confirmed plan, the file paths, the `verify` output and the scope. On
   `needs_revision`, revise and verify again.

## Done when

`verify` prints PASS and the verifier agent's verdict is not `needs_revision`.

## Hands off to

The report back in `references/assessment/overview.md` § Report back.
