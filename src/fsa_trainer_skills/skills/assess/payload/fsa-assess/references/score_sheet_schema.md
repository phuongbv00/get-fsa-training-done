# Score sheet and grade CSV shapes

## Per-submission score sheet

One JSON file per submission, named `<StudentID>.json`, written into the scores
directory:

```json
{
  "std_id": "PhuongBV3",
  "subject": "JPL",
  "submission_type": "ASSIGNMENT",
  "rubric": "jpl_short_assignment_02",
  "tasks": [
    {
      "id": "T1",
      "name": "Entity and Persistence",
      "max": 10.0,
      "weight": 20.0,
      "score": 7.5,
      "comment": "Ánh xạ entity đúng nhưng thiếu ràng buộc unique trên email."
    }
  ],
  "total": 7.5
}
```

Invariants:

- `max` is always `10` — the raw scale.
- `weight` is a percentage, and the weights across tasks sum to 100.
- `total = sum(score * weight) / 100`.
- There is **no** `bonus`, `adjustments`, `deductions`, or submission-level
  `comment`. Caps and deductions are folded into the task score they belong to.

### Comments are learner-facing

One or two sentences per task, in Vietnamese by default, addressed to the
learner. They must never leak how the grading was done — no "chưa chạy được",
no "review tĩnh", no weighted subtotals, no cap arithmetic, and never a
suspicion about copying or AI use. Those belong in the instructor-only cheat
check, which is walled off from grades entirely.

## Aggregated grade CSV

```
Std ID, Name, Comment, T1 (20%), T2 (10%), ..., TN (weight%), Total
```

- `T1..TN` are raw 0-10 task scores in rubric order.
- `Comment` joins the per-task comments as `T1: … | T2: …`.
- Written with a UTF-8 BOM so Excel renders Vietnamese names correctly.
- Row order follows the roster; trainees who dropped are excluded unless named
  explicitly.

A sibling `<name>.legend.txt` maps `T1..TN` back to task ids, names, and
weights. Keep it with the CSV — the column headers alone do not say which task
is which.

## Older sheets

Sheets written before caps moved into task scores may carry `bonus`,
`adjustments`, or `deductions`. They still aggregate to the same total they
always did, and their *reasons* still appear in the Comment column, but their
signed amounts never do.
