# Task — Author open-ended questions

Write the questions of a written theory exam or a written quiz: short prompts a
candidate answers in their own words.

## Inputs

| Input | Notes |
|---|---|
| the confirmed plan | topics, duration, task grouping |
| the scope | the material the questions may draw on |

## Produces

The `## 2. Tasks` section of `<stem>.md`. The rest of the brief follows
`references/assessment/tasks/design/write_brief.md`.

## Steps

### Theory exam — interview questions

Default shape: **20 questions, 4 tasks of 5, 25% each, 90 minutes.** The
Problem Statement is one line ("Answer the 20 questions below."); anything a
question needs — "why", "how would you fix it" — is asked in that question.

Each task mixes three kinds, in this order, so the paper is neither a recall
drill nor a wall of scenarios:

| Per task | Kind | Worth | What it is |
|---|---|---|---|
| 2 | definition | 1.0 each | short and purely theoretical — "What are the JVM, JRE and JDK?" — the marks a prepared candidate can always earn |
| 1 | code reading | tiered | a short snippet: what it prints or does, why, and how to fix it |
| 2 | interview | tiered | a real interview question about mechanism or a trade-off |

Too many scenario or code questions overwhelm a fresher; keep it to one per
task. Every question asks at most 2 things.

- Number questions `**Q1.**` to `**Q20.**` across the whole paper; each task
  groups one topic.
- **Ask, do not enumerate.** "Describe the process from a `.java` file to a
  program running on a machine." The points a strong answer covers go in the
  rubric row, never in the question.
- One question per real interview question. Do not anchor the paper to one
  running domain; a short code fragment inside a question is fine.
- Prefer a question the candidate has to reason about over one they recite:
  give 2 queries — a `LEFT JOIN` filtered in `ON` and in `WHERE` — and ask what
  each returns and why, rather than "where should the filter go?".
- Prefer "what problems does this cause" and "bring it to 3NF" over riddles
  ("which dependency breaks the next normal form?").
- A practical question ("write the query that ...") belongs in a practice exam,
  not here.
- **Never teach the practice exam.** A theory exam usually sits before the
  practice exam of the same module. Leave out what discriminates in the
  practice exam — its tables, class names, and the hard point itself (if Task 4
  of the practice exam is a concurrent order, no theory question walks through
  locking or a lost update on stock) — and tell the instructor not to review
  those points after the theory exam.

### Written quiz — critique an artifact

Default shape: **5 tasks of 20%, 30 minutes, 2-4 sentences each.** The Problem
Statement presents one artifact — a colleague's report with its SQL and plans,
an AI-generated snippet — and each task asks one diagnostic question about it,
with a short title naming the claim under test (`Task 4 - "Safe because it is
a single statement" (20%)`). Deliverable: one text or Markdown file numbered
Task 1 to Task 5.

## Done when

Every question can be answered in the time per question the duration allows,
none of them gives its own answer away, and the paper passes
`FSA assessment verify` in its written form.

## Hands off to

`references/assessment/tasks/design/write_rubric.md` (one row per question),
then `references/assessment/tasks/design/write_answer_template.md` for a theory
exam.
