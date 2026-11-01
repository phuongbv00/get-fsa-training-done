# Task — Export to FAMS's practice mark template

Write assignment or practice-exam marks as the practice mark template FAMS imports: one
row per trainee, a mark per task over the task weights. FAMS has two import
forms; this is the one the assignments and the practice exam share. Quizzes and
the theory exam use the theory mark template,
`references/assessment/tasks/grade/export_fams_theory.md`.

## Inputs

| Input | Notes |
|---|---|
| grade CSV | from `references/assessment/tasks/grade/aggregate.md`, or `merge_retake.md` |
| `roster` | the class; its optional `Account` column names a trainee FAMS knows by another account |
| `template` | the class's practice mark template downloaded from FAMS; optional — without it the form is generated from the roster |
| `topic_code` | `FR_JSKS_JCF`; the template's when it has one |
| `assessment` | the assessment's **code on FAMS**, e.g. `Assignments_1`, `Final Practice Test_1` |
| `marker` | the marker's FPT account, e.g. `PhuongBV3` |
| `date` | the marking date; today by default |

## Produces

An `.xlsx` in the form of FAMS's practice mark template: `Topic`, `Assessment`, `Marker` and
`Date` in C3:C6; one question column per task (`Q1..Qn`, then `Bonus`) with the
task weights in the `Passing Score` row; one row per trainee with the FPT
account, the mark, the comment and the task scores. Name it after the template,
with the assessment's word: `FR_JSKS_JCF_Assignment_Mark_<class>.xlsx`,
`FR_JSKS_JCF_Final_Practice_Test_Mark_<class>.xlsx`.

## Steps

1. Settle every field before running. Take what the user said or the template
   holds; **ask for any you do not know, never guess**:
   - **Assessment** is a code FAMS looks up, not a name to make up. Ask the user
     to read it on FAMS, on the class's assessment list, and say a template's
     own value may belong to another assessment: a template downloaded for the
     practice exam reads `Final Practice Exam_1`, while its cell comment gives
     `Quiz_1`, `Assignments_1`, `Final Theory Test_1`, `Final Practice Test_1`
     as examples. Confirm it even when the template has one.
   - **Topic** is the class's topic code; **Marker** is an FPT account.
2. Run:

   ```bash
   FSA assessment grade export fams practice --grades "<subject_lower>_<archive_token>_grades.csv" \
     --roster "<roster>" --out "<topic_code>_<Word>_Mark_<class>.xlsx" \
     [--template "<FAMS template>.xlsx"] [--topic-code FR_JSKS_JCF] \
     --assessment "<FAMS code>" --marker "<FPT account>" [--date 31/10/2026] \
     --missing-comment "Không nộp bài."
   ```

   Write `--missing-comment` in the comments' language.
3. What it writes, each a FAMS rule:
   - **Account**: the FPT account from the roster, never the personal email a
     template ships with; only a trainee with an `Account` on the roster — a CPL
     trainee — gets that instead.
   - **Who**: the template decides. A graded trainee it lacks is left out (FAMS
     rejects anyone not enrolled) but stays in the grade CSV; a template trainee
     with no grade row is written as 0 with the missing comment, because FAMS
     refuses a blank mark. Without a template, every active roster trainee.
   - **Layout**: the template's label cells stay where they are — its comments
     say they must not move. Its question columns are laid out again to the
     rubric's tasks, and the mark is the form's `SUMPRODUCT` over the weights
     row, its value cached so an importer that reads cells sees it.
4. Pass on everything the command reports — the four fields, who was left out,
   who was written as 0, who is not on the roster, whether the questions were
   laid out again — and ask the user before importing if any is unexpected.
5. When FAMS rejects the import, fix the cause in the grade CSV, roster or
   template and run the export again rather than editing the workbook by hand.

## Done when

The workbook holds one row per class trainee with no blank mark, every mark
matches the grade CSV's `Total`, the four fields are ones the user confirmed,
and every left-out or zeroed trainee has been reported.

## Hands off to

The report.
