# Vietnamese versions

English is the default for everything. A Vietnamese version exists only when
the user asks for one, and it is a **separate sibling file**, never a rewrite of
the original: the English file stays the source, and the translation follows it.

## Naming

The `_vn` suffix goes on the stem, before any suffix that names a derived
format, so a sorted listing keeps each pair together.

| Original | Vietnamese |
|---|---|
| `dbf_practice_exam_01.md`, `.pdf` | `dbf_practice_exam_01_vn.md`, `_vn.pdf` |
| `dbf_quiz_01.csv` (master) | `dbf_quiz_01_vn.csv` |
| `dbf_quiz_01_blooket.csv` | `dbf_quiz_01_vn_blooket.csv` (emitted from the `_vn` master) |
| `fnd_theory_exam_01_coderbyte.json` | `fnd_theory_exam_01_vn_coderbyte.json` |
| `jcf_theory_exam_01_answer_template.md` | `jcf_theory_exam_01_answer_template_vn.md` |
| `fnd_practice_exam_01_template.md` | `fnd_practice_exam_01_template_vn.md` |
| `01_Relational_Modelling.md` (material) | `01_Relational_Modelling_vn.md` |

## What is never translated

- **Rubrics.** `verify` and the grading pipeline parse their headings and rows.
  There is no `_rubric_vn.md`.
- **Structure the tools parse:** the banner and its labels (`> **Code:**`), the
  H1 title, section headings (`## 1. Problem Statement`) and task headings
  (`### Task 1 - ...`), and the `**Qn.**` markers.
- **Code and its names:** code blocks, SQL, query plans, file names, identifiers,
  HTTP status codes, CLI commands.
- **Technical terms.** Keep the term a Vietnamese developer actually uses:
  feature, user story, sprint, backlog, commit, merge, rebase, index, foreign
  key, transaction, instance. A literal translation the reader has to map back
  to English is harder to read, not easier.
- In a master question CSV, only `Question` and `Answer 1-4` are translated;
  `Unit/Lecture` and `Note` stay English.

## Wording

- Never "của bạn". Address the trainee without a possessive ("Viết truy vấn...",
  "Nộp file..."), or with "học viên" when a subject is needed
  (`<câu trả lời của học viên>`).
- Everything in `references/common/style.md` holds: plain words, digits for
  numbers, professional tone.
- A translated brief is held to the same page budget as the original. Render it
  with `--lang vi` and measure it.
