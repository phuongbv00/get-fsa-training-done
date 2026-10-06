# Task — Score a quiz

Turn a quiz platform's results into a score out of 10 per trainee.

## Inputs

| Input | Notes |
|---|---|
| the results | a report workbook (`.xlsx`), or Blooket leaderboard HTML pasted from the report page — one file per paste |
| `questions` | the number of questions in the quiz; required for a leaderboard |
| `roster` | maps nicknames to ids and drops leavers |

## Produces

A CSV of `Std ID, score`.

## Steps

1. Run one of:

   ```bash
   FSA assessment grade quiz --xlsx "<report>.xlsx" --roster "<roster>" --out "<scores.csv>"
   FSA assessment grade quiz --html part1.html --html part2.html --questions 40 \
     --roster "<roster>" --out "<scores.csv>" [--alias "nick=STDID"]
   ```

   A quiz played in parts (a live game, then homework) is one run with one
   `--html` per part; a trainee's best attempt is kept. Different quizzes are
   different runs.
2. The rule: `score = ceil(correct / max(questions, correct + incorrect) * 10, 1 dp)`.
   A trainee who answered fewer questions than the quiz holds is scored out of
   the quiz; one who answered more (game modes repeat questions) out of what
   they answered.
3. Reconcile unmatched nicknames with `--list-unmatched`. Expected when the
   report covers several classes; otherwise each one is a real score being
   dropped — map it with `--alias` and run again.

## Done when

Every roster trainee who sat the quiz has a score, and every unmatched nickname
is explained.

## Hands off to

`references/assessment/tasks/grade/merge_quizzes.md` when several quizzes go in
one table.
