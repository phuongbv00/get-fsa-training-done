# Task — Put quizzes side by side

One table of a class's quiz scores, one column per quiz, in roster order.

## Inputs

| Input | Notes |
|---|---|
| quiz score CSVs | `grade quiz` output, each with a column label |
| `roster` | rows and names |

## Produces

A CSV of `No, ID, Name, <label>...`, on a 10-point scale.

## Steps

```bash
FSA assessment grade merge-quizzes --roster "<roster>" --out "<quizzes.csv>" \
  --quiz "FND 01=<fnd_q1.csv>" --quiz "FND 02=<fnd_q2.csv>"
```

A quiz a trainee did not sit stays blank, not zero: whether it counts as zero
is the programme's decision. Ids the roster does not list are reported.

## Done when

Every active trainee has a row and every reported stray id is explained.

## Hands off to

The report.
