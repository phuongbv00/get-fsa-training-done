# Task — Export to FAMS's theory mark template

Write quiz or theory-exam marks as the theory mark template FAMS imports: one row per
trainee per test, a final mark only. FAMS has two import forms; this is the one
quizzes and the theory exam share. The assignments and the practice exam use
the practice mark template, `references/assessment/tasks/grade/export_fams_practice.md`.

## Inputs

| Input | Notes |
|---|---|
| the marks | **a quiz-score CSV** from `references/assessment/tasks/grade/score_quiz.md` — a module's quizzes, or a multiple-choice theory exam scored the same way; or **a grade CSV** from `references/assessment/tasks/grade/aggregate.md` or `merge_retake.md` — a written theory exam, its `Total` the mark |
| `roster` | the class; its optional `Account` column names a trainee FAMS knows by another account |
| `template` | the class's theory mark template downloaded from FAMS; optional — without it the rows come from the roster |
| `topic_code` | `FR_JSKS_JCF`; needed when there is no template, or the template's TopicCode is blank |
| `assessment` | each test's **code on FAMS**: `Quiz_1`, `Quiz_2`… by column order unless the user says otherwise; for a theory exam, e.g. `Final Theory Exam_1` |

## Produces

An `.xlsx` with one sheet, `Result`: the template's header (or `Email or
Account, Full Name, TopicCode, TestName, Final Mark (/10), Score, Total Score`),
then one block of rows per test. Name it after the template, with the
assessment's word: `FR_JSKS_JCF_Quiz_Mark_<class>.xlsx`,
`FR_JSKS_JCF_Final_Theory_Exam_Mark_<class>.xlsx`.

## Steps

1. Settle the test codes before running. A quiz's default `Quiz_<n>` stands
   unless the user names another. A theory exam's code is one FAMS looks up:
   take the template's `TestName` when every row carries the same one, and
   otherwise **ask the user to read it on the class's assessment list, never
   guess**.
2. Run, with `--quiz-scores` for a module's quizzes:

   ```bash
   FSA assessment grade export fams theory --quiz-scores "<subject_lower>_quiz_scores.csv" \
     --roster "<roster>" --out "<topic_code>_Quiz_Mark_<class>.xlsx" \
     [--template "<FAMS template>.xlsx"] [--topic-code FR_JSKS_JCF] \
     [--assessment "JCF 01=Quiz_1"]
   ```

   or with `--grades` for a written theory exam:

   ```bash
   FSA assessment grade export fams theory --grades "<subject_lower>_<archive_token>_grades.csv" \
     --roster "<roster>" --out "<topic_code>_Final_Theory_Exam_Mark_<class>.xlsx" \
     [--template "<FAMS template>.xlsx"] [--topic-code FR_JSKS_JCF] \
     [--assessment "Final Theory Exam_1"]
   ```

   For a retake exported apart from the first attempt, add `--graded-only`:
   the form lists only the trainees who sat it, rather than writing 0 for
   those who passed the first time. A retake's cap is applied to its grade
   CSV before this export.
3. What it writes, each a FAMS rule learned from a rejected import:
   - **Account**: the FPT account id from the roster, never the personal email a
     template ships with. Only a trainee with an `Account` on the roster — a
     CPL trainee, known by personal email — gets that instead.
   - **Who**: the template decides. A trainee with marks it lacks is left out
     of the workbook (FAMS rejects anyone not enrolled, or whose status forbids
     a mark) but stays in the source CSV; a template trainee with no marks is
     written as 0 and reported. Without a template, every active roster trainee. With
     `--graded-only`, only the trainees with marks.
   - **Marks**: Final Mark and Score are the mark out of 10, Total Score is 10.
     FAMS refuses a blank mark, so a missed test is written as 0.
4. Pass on everything the command reports — who was left out, who was written
   as 0, who is not on the roster — and ask the user before importing if any of
   it is unexpected.
5. When FAMS rejects the import, its error CSV names sheet cells: fix the cause
   in the source CSV, roster or template and run the export again rather than
   editing the workbook by hand.

## Done when

The workbook holds one row per class trainee per test with no blank mark, each
test carries a code the user confirmed or the template gave, and every
left-out or zeroed trainee has been reported.

## Hands off to

The report.
