# Task — Score a module's quizzes

Turn a module's results CSV into a score out of 10 per trainee per quiz.

## Inputs

| Input | Notes |
|---|---|
| results CSV | from `references/assessment/tasks/grade/ingest_quiz.md` |
| `roster` | maps nicknames to ids, names the row order, drops leavers |
| `questions` | questions per quiz; needed for rows without an unattempted count (leaderboards, screenshots). Ask when you do not know it |

## Produces

`<subject_lower>_quiz_scores.csv`: `No, ID, Name, <one column per quiz>`,
active trainees in roster order, quizzes in the order the results CSV first
names them. A quiz a trainee did not sit is blank.

## Steps

1. Run:

   ```bash
   FSA assessment grade quiz-module --results "<subject_lower>_quiz_results.csv" \
     --roster "<roster>" --questions 40 [--questions-for "JCF 03=30"] \
     --out "<subject_lower>_quiz_scores.csv" [--alias "nick=STDID"]
   ```

2. The rule, one decimal, rounded up: correct ÷ the questions the trainee was
   set × 10, where "set" is `max(answered, correct + incorrect) + unattempted`.
   A row without `unattempted` is set the quiz's question count, or what the
   player answered when game modes repeated questions and that is more. A
   trainee with several attempts at one quiz keeps the best.
3. Reconcile every nickname the command reports as not on the roster. Most are
   loose spellings of a roster id (`Hieund`, `nguyenhk7-`, a full name): map each
   with `--alias` and run again. Ask the user about any you cannot place; one
   left unmapped is a real score dropped.

## Done when

Every unmatched nickname is mapped or explained, and every blank in the score
CSV is a quiz the trainee did not sit.

## Hands off to

`references/assessment/tasks/grade/export_fams.md`.
