# Task — Export to FAMS

Write a module's quiz scores as the workbook FAMS imports.

## Inputs

| Input | Notes |
|---|---|
| score CSV | from `references/assessment/tasks/grade/score_quiz.md` |
| `template` | the class's mark template downloaded from FAMS; optional — without it the rows come from the roster |
| `roster` | its optional `Account` column names a trainee FAMS knows by another account |
| `topic_code` | `FR_JSKS_JCF`; needed when there is no template, or the template's TopicCode is blank |

## Produces

An `.xlsx` with one sheet, `Result`: the template's header (or `Email or
Account, Full Name, TopicCode, TestName, Final Mark (/10), Score, Total Score`),
then one block of rows per quiz, named `Quiz_1`, `Quiz_2`… in the score CSV's
column order. Name it after the template, with `Quiz` for its assessment word:
`FR_JSKS_JCF_Quiz_Mark_<class>.xlsx`.

## Steps

1. Run:

   ```bash
   FSA assessment grade fams-export --scores "<subject_lower>_quiz_scores.csv" \
     --template "<FAMS template>.xlsx" --roster "<roster>" \
     --out "<topic_code>_Quiz_Mark_<class>.xlsx" [--topic-code FR_JSKS_JCF] \
     [--test-name "JCF 01=Quiz_1"]
   ```

2. What it writes, each a FAMS rule learned from a rejected import:
   - **Account**: the FPT account id from the roster, never the personal email a
     template ships with. Only a trainee with an `Account` on the roster — a
     CPL trainee, known by personal email — gets that instead.
   - **Who**: the template decides. A scored trainee it lacks is left out of the
     workbook (FAMS rejects anyone not enrolled, or whose status forbids a
     mark) but stays in the score CSV; a template trainee with no scores is
     written as 0 and reported. Without a template, every active roster trainee.
   - **Marks**: Final Mark and Score are the mark out of 10, Total Score is 10.
     FAMS refuses a blank mark, so a missed quiz is written as 0.
3. Pass on everything the command reports — who was left out, who was written
   as 0 — and ask the user before importing if any of it is unexpected.
4. When FAMS rejects the import, its error CSV names sheet cells: fix the cause
   in the score CSV, roster or template and run the export again rather than
   editing the workbook by hand.

## Done when

The workbook holds one row per class trainee per quiz with no blank mark, and
every left-out or zeroed trainee has been reported.

## Hands off to

The report.
