# Task — Author multiple-choice questions

Write the master question CSV a quiz or a multiple-choice theory exam is
emitted from.

## Inputs

| Input | Notes |
|---|---|
| the confirmed plan | count, Bloom and difficulty mix, unit mix, option count, time map |
| the scope | the topics and learning objectives trained, e.g. a syllabus's objectives and session plan |

## Produces

`<stem>.csv`, **instructor-only** — it holds the answers.

## Steps

1. Read `references/assessment/question_guidelines.md` in full before drafting.
2. Write exactly these twelve columns:

   ```
   No,Unit/Lecture,Bloom Level,Difficulty,Question,Answer 1,Answer 2,Answer 3,Answer 4,Correct Answer(s),Time Limit (sec),Note
   ```

   - `Correct Answer(s)` is the 1-based option number: `2`, or `1,3` for multi.
   - All four answers are filled for every question.
   - `Time Limit (sec)` follows the confirmed map: a quiz's live-game timings
     (Easy 5, Medium 10, Hard 20 by default), or a theory exam's thinking-time
     map from the level (typically 30 / 45 / 75).
   - `Note` is your one-line design rationale.
3. Spread the correct answers across positions; the emitter reorders them only
   where a platform demands it.
4. Keep every question importable:
   - **No backticks.** Neither platform renders Markdown. Write code fragments
     as bare text; name a character in words if the question is about it.
   - **No raw tags or generics.** `<CartPanel />`, `</>`, `List<String>` are
     swallowed as markup. Name it in prose ("a CartPanel element", "a List of
     String"), or, when the literal syntax is what is assessed, space every
     bracket: `List < String >`. Operators (`->`, `>=`, `<>`) are fine.
5. For a theory exam the marks count, so questions must discriminate: at
   `UP_SKILL` and above most are Apply and Analyze, written as a situation, a
   symptom or a decision. A recall question dressed in a scenario is still
   recall — if it can be answered without reading the scenario, rewrite it.
   A multiple-choice theory exam keeps the interview style of the written one:
   about half concept questions ("What is the difference between X and Y?",
   "Which statement about X is true?") and half short code-trace or scenario
   questions in a neutral domain. It is not a quiz on how the lecture built
   things.
6. Ask about the topic, never about the material: no "the lecture recommends
   X — why?" or "theo bài giảng". State X as the situation and ask why
   (`references/assessment/overview.md` § Standing rules).
7. Run every question whose key depends on what code outputs, on the exact
   JDK, database or framework version the module trains, through
   `FSA assessment sandbox run` (`references/common/tasks/run_in_sandbox.md`).
   A key never rests on what the code looks like it prints.
8. Compare against what learners have already seen: pass every quiz of the
   module and every earlier theory exam — written briefs included — as
   `--prior` to `FSA assessment verify`. Read each question it flags next to
   the earlier one and replace any that asks the same thing.

## Done when

`FSA assessment verify --type <quiz|theory_exam> --master <stem>.csv --level
<LEVEL> --expect-count N` passes, and the actual Bloom, difficulty and unit
tallies match the plan, no `--prior` overlap is left unread, and every
code-output key was run.

## Hands off to

`references/assessment/tasks/design/emit_imports.md`.
