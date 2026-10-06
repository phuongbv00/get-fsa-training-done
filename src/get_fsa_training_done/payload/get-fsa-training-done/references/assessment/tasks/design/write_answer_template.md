# Task — Write the answer template

The Markdown file a candidate fills in and submits: a written theory exam's
answer sheet, or a practice exam's worksheet with its tables already drawn.

## Inputs

| Input | Notes |
|---|---|
| the brief | finished, with its task and `**Qn.**` numbering |

## Produces

Learner-facing, given out with the brief:

- theory exam: `<stem>_answer_template.md`;
- practice exam: `<stem>_template.md`, or a name for the artifact it holds
  (`<stem>_plan_analysis_template.md`).

## Steps

1. Open with the title and a candidate line, then one short instruction
   paragraph: rename the file, answer under the matching heading, put code in
   fenced blocks, leave the headings alone.

   ```markdown
   # Final Theory Exam - <Name> - <CODE>

   > **Candidate:** <your FPT account>

   Rename this file to `<subj>_t_exam_01_<your FPT account>.md`. Answer each
   question under its heading. Leave the headings as they are.

   ---

   ## Task 1 - <exact task name from the brief>

   **Q1.**

   <your answer>
   ```

2. One `## Task N - <name>` heading per task, named exactly as in the brief, and
   one `**Qn.**` slot per question, in order.
3. **Never copy a question into the template.** It is opened, edited and handed
   back, so whatever it contains travels further than the brief does — a
   template that quotes the questions is a second copy of the paper.
4. For a practice exam worksheet, draw the tables the task asks for, with
   column headers only, so no time goes into Markdown layout. Do not draw in
   the answer's structure beyond what the brief already states.

## Done when

`FSA assessment verify ... --answer-template <file>` reports no errors: the
headings match, every question has a slot, the candidate line is there, and no
question text appears.

## Hands off to

`references/assessment/tasks/design/render_pdf.md`. A Vietnamese version of the
template follows `references/common/tasks/translate_vn.md`.
