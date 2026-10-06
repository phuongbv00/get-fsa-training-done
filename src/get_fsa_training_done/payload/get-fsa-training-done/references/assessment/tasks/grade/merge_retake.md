# Task — Merge a retake

Combine a first attempt's grade CSV with a retake's into one result per
trainee, under the programme's retake policy.

## Inputs

| Input | Notes |
|---|---|
| first-attempt grade CSV | `grade aggregate` output |
| retake grade CSV | `grade aggregate` output, graded with the retake paper's own rubric |
| policy | cap (default 6), keep (`higher` by default, or `retake`), and any voided retakes |

## Produces

A merged grade CSV. Both inputs are left as they are, so the separate per-attempt
CSVs stay available.

## Steps

1. Confirm the policy with the user; the defaults are the FR programme's:
   - a retake earns **at most 6**, its task scores left as graded;
   - the **higher effective total** wins — the retake's after its cap;
   - a retake **voided** (for example for cheating) leaves the first attempt.
2. Run:

   ```bash
   FSA assessment grade merge-retake --first "<first.csv>" --retake "<retake.csv>" \
     --roster "<roster>" --out "<merged.csv>" \
     [--cap 6] [--keep higher] [--void-ids <ID>...] \
     [--cap-note "Thi lại: điểm tổng tối đa {cap}."]
   ```

   The attempt kept supplies the task scores and the comment. Write `--cap-note`
   in the comment language.
3. When the papers have different task lists, the T columns lose their weights
   and hold each kept attempt's own tasks; say so in the report.

## Done when

Every trainee has one row, and the report names who kept the retake, who was
capped and whose retake was voided.

## Hands off to

The report.
