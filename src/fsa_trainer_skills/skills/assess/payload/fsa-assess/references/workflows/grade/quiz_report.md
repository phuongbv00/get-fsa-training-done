# Workflow — score a quiz report

A quiz platform exports a participant report as a workbook. This turns it into
per-trainee scores. It is **not** the assignment pipeline — do not preprocess,
do not batch, do not write score sheets.

## 0. Inputs

| Input | Notes |
|---|---|
| report workbook | the platform's `.xlsx` export |
| `roster` | to map nicknames to roster ids and drop leavers |
| output path | where the score CSV goes |

## 1. Score it

```bash
FSA grade quiz \
  --xlsx    "<report>.xlsx" \
  --roster  "<roster>" \
  --out     "<results_dir>/<report>_scores.csv" \
  --converted-csv "<results_dir>/<report>.sheet2.csv"
```

The participant summary is the workbook's second sheet; `--sheet-index` changes
that if the export differs.

`--converted-csv` also writes the raw sheet, which is worth keeping — it is the
only record of what the platform actually reported once the workbook is gone.

## 2. The scoring rule

```
expected_total = max(answered, correct + incorrect) + unattempted
score          = ceil(correct / expected_total * 10, to 1 decimal)
```

Unattempted questions count against the trainee — the denominator is what they
were asked, not what they answered. `max(answered, correct + incorrect)` guards
against reports whose "Qs Answered" disagrees with correct plus incorrect;
taking the larger keeps anyone from being scored out of fewer questions than
they actually saw.

## 3. Read the note about unmatched nicknames

Nicknames are matched against the roster exactly, case-insensitively. Anyone
unmatched is left out of the CSV and reported as a count.

**This is expected when the report covers the whole cohort** and you are scoring
one class — the others simply are not on this roster. It is a real problem when
the report covers only this class, because then an unmatched nickname is a typo
and a genuine score is being dropped.

Use `--list-unmatched` to see them, and reconcile by hand before delivering the
CSV.

## 4. Report

The output has two columns, `Std ID` and `score`. Tell the user how many scored,
how many were excluded as dropped, and how many nicknames went unmatched — with
your reading of whether that count is expected here.
