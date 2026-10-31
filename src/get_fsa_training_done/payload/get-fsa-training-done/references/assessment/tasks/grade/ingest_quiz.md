# Task — Ingest quiz results

Gather one module's quiz results, whatever their source, into one results CSV.

## Inputs

| Input | Notes |
|---|---|
| the results | any mix of report workbooks (`.xlsx`), Blooket leaderboard HTML pasted from the report page, and screenshots of a leaderboard (Blooket or another platform) |
| `quiz` | the label each source's scores go under, `<SUBJECT> NN`: `JCF 01` |
| `part` | which run of the quiz a source is, when there are several: `live`, `HW` |

## Produces

`<subject_lower>_quiz_results.csv`, a row per player per attempt:

```
quiz,part,nickname,correct,incorrect,answered,unattempted
```

`answered` and `unattempted` stay blank when the source does not give them (a
leaderboard, a screenshot); the score step then counts the quiz's question
total instead.

## Steps

1. A workbook or leaderboard HTML goes in through the CLI, which appends to the
   file and writes the header on a new one:

   ```bash
   FSA assessment grade quiz-ingest --results "<subject_lower>_quiz_results.csv" \
     --quiz "JCF 01" --part live --html part1.html [--html part2.html]
   FSA assessment grade quiz-ingest --results "<subject_lower>_quiz_results.csv" \
     --quiz "JCF 02" --xlsx "<report>.xlsx" [--sheet-index 2]
   ```

2. A screenshot you read yourself and append its rows to the same file, one
   per player, in the header's column order:
   - the nickname exactly as shown, typos and stray characters included —
     matching it to the roster is the next task's job, and an `--alias` there
     records the decision;
   - correct and incorrect from the green and red parts of the accuracy bar; a
     bar with one colour has 0 for the other;
   - `answered` and `unattempted` blank.

   A leaderboard that scrolls is several screenshots; take every player once.
3. The same quiz played twice (a live game, then homework for those who missed
   it) is two sets of rows with the same `quiz` and different `part`s. The next
   task keeps each trainee's best attempt.

## Done when

Every source the user sent is in the results CSV, under the right quiz label.

## Hands off to

`references/assessment/tasks/grade/score_quiz.md`.
