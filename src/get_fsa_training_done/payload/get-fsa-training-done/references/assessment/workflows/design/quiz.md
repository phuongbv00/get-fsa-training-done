# Workflow — quiz

A short check on a unit, in one of two forms. Confirm the form in planning.

| Form | What the trainee does | Produces |
|---|---|---|
| `mcq` | plays a live game (Blooket) | `<stem>.csv` (instructor-only master), `<stem>_blooket.csv` |
| `oe` | writes short answers about an artifact | `<stem>.md`, `<stem>_rubric.md`, `<stem>.pdf` |

## Multiple choice

| Step | Task | For a quiz |
|---|---|---|
| 1 | `references/assessment/tasks/design/plan_scope.md` | default 40 questions, 30 minutes, 4 options, Easy 5s / Medium 10s / Hard 20s; confirm with `FSA assessment levels show --level <L> --count 40` and **draft nothing until confirmed** |
| 2 | `references/assessment/tasks/design/author_mcq.md` | one unit bucket per topic in scope |
| 3 | `references/assessment/tasks/design/emit_imports.md` | `emit blooket` |
| 4 | `references/assessment/tasks/design/verify.md` | `--type quiz --master ... --blooket ... --expect-count 40`, then tally Bloom, unit and difficulty against the plan; verifier `references/assessment/verifiers/quiz.md` |
| 5 | `references/common/tasks/translate_vn.md` | only on request: a `_vn` master, emitted to `_vn_blooket.csv` |

## Written

| Step | Task | For a quiz |
|---|---|---|
| 1 | `references/assessment/tasks/design/plan_scope.md` | default 5 tasks of 20%, 30 minutes |
| 2 | `references/assessment/tasks/design/write_brief.md` | `Code: <LEVEL>_<SUBJ>_Q_<seq>`; deliverable: one file answering Task 1 to Task 5 |
| 3 | `references/assessment/tasks/design/author_oe_questions.md` | § Written quiz — critique an artifact |
| 4 | `references/assessment/tasks/design/write_rubric.md` | one row per question |
| 5 | `references/assessment/tasks/design/render_pdf.md` | 30 minutes is a 2-page budget |
| 6 | `references/assessment/tasks/design/verify.md` | `--type quiz --brief ... --rubric ... --pdf ...`; verifier `references/assessment/verifiers/quiz.md` |
| 7 | `references/common/tasks/translate_vn.md` | only on request |
