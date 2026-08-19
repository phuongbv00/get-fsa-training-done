# Question-writing standard (quiz / theory_exam)

Read this before drafting any multiple-choice question for the question-set
branch (`quiz`, `theory_exam`). It exists to prevent quizzes that don't
actually measure the Learning Objective (LO).

## Problem this guards against

- Question drifts from the LO — e.g. the LO requires "apply" but the question
  only tests "recall".
- Learner can answer from general/prior knowledge without needing the course
  content.
- Options are trivially guessable — the correct one is obviously right, or
  the wrong ones are obviously silly.
- Question is harder than the LO requires — someone who can actually do the
  job in practice still can't answer it, because the wording is confusing
  rather than the concept being hard.

## Question type — derive from the LO's Bloom level

- **Remember** → recall, recognize.
- **Understand** → give a definition, a property/characteristic, an example;
  or evaluate something against a stated criterion.
- **Apply** → resolve a scenario/problem (identify → analyze → propose a
  solution → verify → conclude); or predict the cause/effect of a
  situation.

Do not write a Remember-level question for an Apply-level LO, or vice versa.

## Stem (question text)

- Must actually assess the LO — not a nearby but different fact.
- Force the learner to use information given *in the stem* to decide, rather
  than answer from memorized/generic knowledge alone.
- Short, information-sufficient — no more, no less than needed.
- Simple sentence structure, phrased as a positive statement — avoid
  negatives ("which of the following is NOT...").
- State the task explicitly: "choose the correct answer" vs "choose the most
  appropriate answer".
- Never leak hints that let the learner guess without knowing the content.
- Use media (image, screenshot, audio) when the real-world task itself
  requires reading/hearing something.

## Options (answers)

- Similar length across all options.
- Concise.
- Plain, familiar wording — no unexplained jargon unless the job itself
  requires recognizing that term.
- All options share the same grammatical structure as the stem and each
  other.
- No leaked hints that single out the correct option (e.g. one option much
  more detailed/specific than the rest).
- No "All of the above" / "None of the above".
- No "both A and B" / "both A and C" as an option — if multiple options can
  be correct, make it an explicit multi-select question instead.
- Use at least 4 answer options by default for quiz and theory exam
  generation. Add more only when the confirmed structure requires it.

## Distractors (wrong options)

- Every wrong option should look plausible — "half-right" is not the same as
  right, but it should not look absurd.
- Base distractors on real mistakes learners commonly make (including
  mistakes you yourself would be tempted to make) — that is what makes a
  distractor diagnostic rather than decorative.

## Plain-text formatting (Blooket / Coderbyte import)

Question and answer text lands in import platforms that render **plain text
only** — no Markdown — and that **parse what you send as markup**. Anything
tag-shaped is swallowed and the learner never sees it.

- **No backticks.** Do not wrap code fragments, identifiers, keywords, or
  literals in backticks. They either break the import or appear verbatim to
  the learner. Write `List.of(1, 2)` as bare text: List.of(1, 2). The same
  goes for triple-backtick fences — put short code inline, and if a snippet is
  too long to read inline, the question is too long for a quiz.
- No other Markdown either: no `**bold**`, no `_italics_`, no `#` headings,
  no `[links](…)`.
- **No raw tags or generics.** `<CartPanel />`, `</>`, `<div>`, `List<String>`
  and `ResponseEntity<BookResponse>` all vanish mid-sentence on import. Prefer
  to **name the thing in prose** — "a CartPanel element", "a JSX fragment", "a
  div wrapper replaced by a section wrapper", "a JpaRepository of Book with a
  Long id". Only when the literal syntax is itself the assessed content, space
  every bracket so none touches a letter, digit or slash: List < String >,
  Map < K, V >, < CartPanel / >, < > ... < / >.
- When a tag would otherwise repeat across the stem and all four options, that
  is a signal to **restructure**: hoist the markup into the stem as a
  placeholder and let the options carry only the part under test — the
  condition, the attribute, the type argument. Shorter, more comparable
  options are better questions regardless of the platform.
- Language operators are safe as-is with normal outer spacing, because they
  never read as tags: user -> user.isActive(), score >= 5,
  Country <> 'Germany'.

## Quick self-check before finalizing a question

1. Does this question measure the stated LO at its stated Bloom level?
2. Could someone answer this correctly using only outside/common knowledge,
   without having learned the lecture content?
3. Is the correct option identifiable by its *shape* (length, specificity,
   phrasing) rather than its content?
4. Are all distractors things a real learner might actually pick?
5. Is the difficulty appropriate — someone who can do the task in practice
   should be able to answer it?
6. Is the stem and every option free of backticks, other Markdown, and
   anything tag-shaped that the import platform would swallow?

If any answer is "no" (for #1, #2, #4, #6) or the question feels off on #3/#5,
rewrite before adding it to the question-set CSV.
