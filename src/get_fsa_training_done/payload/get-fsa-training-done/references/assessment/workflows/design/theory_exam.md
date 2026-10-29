# Workflow — theory exam

A graded, timed exam on concepts, in one of two forms. Confirm the form in
planning. Either way it is pure theory and stands alone: no shared domain with
the practice exam, no reference to labs or assignments.

| Form | What the candidate does | Produces |
|---|---|---|
| `oe` | answers interview questions in writing | `<stem>.md`, `<stem>_rubric.md`, `<stem>_answer_template.md`, `<stem>.pdf` |
| `mcq` | answers multiple choice on Coderbyte | `<stem>.csv` (instructor-only master), `<stem>_coderbyte.json` |

## Written — interview questions

| Step | Task | For a theory exam |
|---|---|---|
| 1 | `references/assessment/tasks/design/plan_scope.md` | default 20 questions, 4 tasks of 5, 25% each, 90 minutes; score target and profile estimate |
| 2 | `references/assessment/tasks/design/write_brief.md` | `Code: <LEVEL>_<SUBJ>_TE_<seq>`; Topics may list the outcome codes; deliverable: the completed template, renamed `<subj>_t_exam_<seq>_<fpt_account>.md`, nothing else |
| 3 | `references/assessment/tasks/design/author_oe_questions.md` | § Theory exam — interview questions |
| 4 | `references/assessment/tasks/design/write_rubric.md` | one row per question; definitions by point, the rest in Base/Mechanism/Strong tiers |
| 5 | `references/assessment/tasks/design/write_answer_template.md` | headings and `**Qn.**` slots only, never the questions |
| 6 | `references/assessment/tasks/design/render_pdf.md` | 90 minutes is a 3-page budget |
| 7 | `references/assessment/tasks/design/verify.md` | `--type theory_exam --brief ... --rubric ... --answer-template ... --pdf ...`; verifier `references/assessment/verifiers/theory_exam.md` |
| 8 | `references/common/tasks/translate_vn.md` | only on request: the brief and the answer template |

## Multiple choice

| Step | Task | For a theory exam |
|---|---|---|
| 1 | `references/assessment/tasks/design/plan_scope.md` | the level's non-quiz time map (typically Easy 30s, Medium 45s, Hard 75s) |
| 2 | `references/assessment/tasks/design/author_mcq.md` | apply the level's Bloom mix strictly; interview style — half concept, half code-trace or scenario in a neutral domain; run every code-output key |
| 3 | `references/assessment/tasks/design/emit_imports.md` | `emit coderbyte`; index 0 is always correct |
| 4 | `references/assessment/tasks/design/verify.md` | `--type theory_exam --master ... --coderbyte ... --prior <each quiz and earlier theory exam>`; verifier `references/assessment/verifiers/theory_exam.md` |
| 5 | `references/common/tasks/translate_vn.md` | only on request: `_vn` master, emitted to `_vn_coderbyte.json` |

## Retake

A retake paper is a new paper in either form, numbered on (`_02` after
`_01`), never a reshuffle of the first. It may ask the core concepts again, but
no question or scenario that appeared in the module's quizzes, the first
theory exam or the practice exam: pass all of them as `--prior`. Grading and
merging the two attempts is `references/assessment/workflows/grade/retake.md`.
