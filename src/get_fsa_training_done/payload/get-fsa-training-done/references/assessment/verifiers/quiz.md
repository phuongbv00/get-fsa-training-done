# Quiz Verifier Agent

Use this verifier after generating or editing a `quiz`: a multiple-choice master
CSV and its import file, or a written quiz's brief and rubric. Check the section
for the form being verified.

## Inputs

- Master CSV path.
- Generated Blooket CSV path, if any.
- Generated Coderbyte JSON path, if any.
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
- Question stems are concise, positive, and assess the intended Bloom level.
- Distractors are plausible and based on realistic learner mistakes.
- Questions do not use "All of the above", "None of the above", or "both A and
  B" style options.
- Correct answers in import files are derived from the master CSV and remain
  consistent.
- The Blooket template title row has exactly eight CSV fields
  (`Blooket Import Template,,,,,,,`), so comma delimiter detection is stable
  before any question or option needs CSV quotes.
- Nothing tag-shaped survives in stems or options: no raw JSX/HTML elements
  (`<CartPanel />`, `</>`, `<div>`) and no unspaced generics (`List<String>`,
  `Map<K,V>`) — Blooket parses these as markup and the learner never sees them.
  Elements are named in prose ("a CartPanel element", "a JSX fragment"), or,
  where the literal syntax is the assessed content, every bracket is spaced
  (`List < String >`, `new ArrayList < > (items)`, `< CartPanel / >`). Language
  operators such as Java `->`, `>=`, `<=`, `>>` and SQL `<>` remain intact.
- No backtick characters appear in any question stem or answer option, in the
  master CSV or in the Blooket CSV — Blooket renders plain text only, and
  backticks break the import or show up literally. Code fragments are written
  bare, without surrounding backticks, and no other Markdown (bold, italics,
  headings, links, code fences) is present either.
- Quiz content stays inside the confirmed module/topic scope.

- **Level calibration.** Compare the actual Bloom and difficulty mix against
  the confirmed level's row in `references/assessment/levels.md`, and say whether the
  questions genuinely sit where their labels claim. A question labelled Apply
  that a candidate can answer from a definition mis-calibrates the set, because
  the counts were checked against the target and now describe something untrue.

## Written form

Inputs are the brief, the rubric, the PDF, the structural verifier output, and
the scope. Check:

- The Problem Statement presents one concrete artifact to critique, and every
  task asks one diagnostic question about it.
- Each task is answerable in 2-4 sentences, and the paper fits its duration.
- Task titles name the claim under test without giving away the verdict.
- The rubric gives, per task, the points a correct diagnosis covers.

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
