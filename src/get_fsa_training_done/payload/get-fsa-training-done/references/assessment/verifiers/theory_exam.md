# Theory Exam Verifier Agent

Use this verifier after generating or editing a `theory_exam`: a multiple-choice
master CSV and its import file, or a written exam's brief, rubric and answer
template. Check the section for the form being verified.

## Inputs

- Master CSV path.
- Generated Coderbyte JSON path, if any.
- Generated Blooket CSV path, if any.
- Confirmed question-set plan.
- Structural verifier output.
- Relevant lecture/topic scope.

## Verification Focus

Check both structure and content:

- Master CSV follows the required columns and contains one row per question.
- Actual question count, Bloom distribution, unit distribution, difficulty
  distribution, answer option count, and time limits match the confirmed plan.
- Each question has at least 4 plausible answer options.
- Time limits use the confirmed mapping, defaulting to the level's non-quiz map
  (typically Easy = 30, Medium = 45, Hard = 75 seconds) — not the quiz's 5/10/20,
  which exist for a live game.
- Coderbyte JSON follows the template: top-level `mc_questions`, correct answer
  first for single-answer questions, and `correctAnswers`/`allRequired` for
  multi-answer questions.
- No backtick characters appear in any question stem or answer option, in the
  master CSV or in the Coderbyte JSON — Coderbyte renders plain text only, and
  backticks break the import or show up literally. Code fragments are written
  bare, without surrounding backticks, and no other Markdown (bold, italics,
  headings, links, code fences) is present either.
- Nothing tag-shaped survives in stems or options: no raw JSX/HTML elements
  (`<CartPanel />`, `</>`, `<div>`) and no unspaced generics (`List<String>`,
  `ResponseEntity<BookResponse>`) — Coderbyte parses these as markup and the
  learner never sees them. Elements are named in prose ("a CartPanel element",
  "a JSX fragment"), or, where the literal syntax is the assessed content,
  every bracket is spaced (`List < String >`, `< CartPanel / >`). Language
  operators (`->`, `>=`, `<=`, SQL `<>`) are left intact.
- Question stems measure theory understanding/application, not code style or
  unrelated implementation preference.
- Apply-level questions require scenario reasoning, not simple recall.
- Distractors reflect realistic misconceptions from the module.
- Content stays inside the confirmed scope and avoids mentioning hidden source
  material or assessment scaffolding when the user requested that boundary.
- No answer keys are exposed in learner-facing import files beyond the
  Coderbyte convention required for import.

- **Level calibration.** Compare the actual Bloom and difficulty mix against
  the confirmed level's row in `references/assessment/levels.md`, and say whether the
  questions genuinely sit where their labels claim. A question labelled Apply
  that a candidate can answer from a definition mis-calibrates the set, because
  the counts were checked against the target and now describe something untrue.

## Written form

Inputs are the brief, the rubric, the answer template, the PDF, the structural
verifier output, and the scope. Check:

- Each question is asked the way an interviewer asks it: short, naming the
  subject, without listing the points of a good answer. Those points are in the
  rubric row instead.
- The paper is pure theory and stands alone: no running domain shared with the
  practice exam, no reference to a lab or an assignment, no "write the query
  that ..." task.
- Questions that can be reasoned about are posed that way (predict and explain
  two queries' results) rather than as recall.
- The wording is plain and unambiguous for a trainee reading a second language,
  numbers are digits, and the Vietnamese version (if any) never says "của bạn".
- Every rubric row lists the points a strong answer covers, and a bare
  definition is capped at half the row.
- The answer template has the task headings and `**Qn.**` slots only, and none
  of the question text.
- The question count fits the duration: about 3 minutes per question at the
  default 20 in 60 minutes.

## Output

Return:

```text
VERDICT: pass | needs_revision
STRUCTURE: <CSV/import notes>
CONTENT: <question quality notes>
DISTRIBUTION: <actual vs expected notes>
REVISIONS_REQUIRED:
- <actionable item, or "none">
```

