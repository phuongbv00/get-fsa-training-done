# Theory Exam Verifier Agent

Use this verifier after generating or editing a `theory_exam` master CSV and
import file(s).

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
- Time limits use the confirmed mapping, defaulting to Easy = 5, Medium = 10,
  Hard = 20 seconds.
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
  the confirmed level's row in `references/levels.md`, and say whether the
  questions genuinely sit where their labels claim. A question labelled Apply
  that a candidate can answer from a definition mis-calibrates the set, because
  the counts were checked against the target and now describe something untrue.

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

