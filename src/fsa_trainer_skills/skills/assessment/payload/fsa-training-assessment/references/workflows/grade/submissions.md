# Workflow — grade submissions

For assignments and exams. Pipeline:

**preprocess → plan → grade in parallel batches → aggregate**

The scripts do the mechanical work. **You do the grading judgement**, and you
never run the learner's code.

## 0. Inputs

Ask for all of these before touching the filesystem:

| Input | Notes |
|---|---|
| `roster` | CSV with `ID`, `Name`, `Status` columns |
| `submissions_dir` | folder holding the raw uploads |
| `results_dir` | where scores and the grade CSV go |
| `subject`, `submission_type` | e.g. `JPL`, `ASSIGNMENT` |
| `brief_path`, `rubric_path` | the assessment being graded |
| batch count | default 4 |

Echo the resolved absolute paths and wait for a go-ahead.

## 1. Preprocess

```bash
FSA assessment grade preprocess \
  --roster  "<roster>" \
  --src     "<submissions_dir>" \
  --subject "<SUBJECT>" \
  --type    "<TYPE>" \
  --out     "<submissions_dir>/_preprocessed"
```

Extracts archives, strips junk and redundant nesting, and lays out one folder
per trainee as `<SUBJECT>_<TYPE>_<STDID>`. Nothing in the source is modified.

Read the report before continuing. Three things need a decision:

- **UNKNOWN-ID** — the filename matched no roster id. Resolve it by hand; it is
  usually a trainee who renamed their archive.
- **Did NOT submit** — confirm with the user rather than assuming a zero.
- **Extraction FAILED** — a corrupt or unusual archive. `FSA doctor` reports
  which extractors this machine has.

## 2. Plan the batches

```bash
FSA assessment grade plan \
  --preprocessed "<submissions_dir>/_preprocessed" \
  --scores       "<results_dir>/_scores" \
  --subject      "<SUBJECT>" \
  --type         "<TYPE>" \
  --roster       "<roster>" \
  --batches      4
```

Prints JSON. Anyone who already has a score sheet is skipped, so a re-run picks
up exactly the leftovers.

## 3. Grade each submission

Spawn one grading subagent per batch when there are more than a handful;
otherwise grade inline. Give each subagent the brief, the rubric, its list of
folders, and `references/score_sheet_schema.md`.

Rules that hold for every submission:

- **Read the artifacts as evidence. Do not execute anything.** Not the build,
  not the tests, not a single script.
- **Correct and small beats broken and feature-rich.** A submission that does
  three of five tasks properly outscores one that half-implements all five.
- **Claims only count when the submission backs them up.** A README asserting a
  feature exists is not the feature.
- Score each task on 0–10, then fold that task's own caps and deductions — its
  `### Tn` subsection of the rubric's section 4, plus anything under
  `### Every task` — into the number. Nothing is subtracted from the total
  afterwards; there is no separate adjustment step.
- Write one or two sentences of **learner-facing English** feedback per task.
  Never leak grading method, never mention how the file was reviewed, never
  raise a suspicion about copying or AI use.

Write one `<StudentID>.json` per submission into the scores directory, in the
shape given by `references/score_sheet_schema.md`.

## 4. Aggregate

```bash
FSA assessment grade aggregate \
  --scores "<results_dir>/_scores" \
  --roster "<roster>" \
  --out    "<results_dir>/<subject_lower>_<archive_token>_grades.csv"
```

Writes the grade CSV plus a `.legend.txt` mapping `T1..TN` back to task ids.
Keep them together — the headers alone do not say which task is which.

Trainees who dropped are excluded. To include one anyway, name them:
`--include-dropped-ids <StudentID>`.

## 5. Report

Give the user: how many were graded, who did not submit, any UNKNOWN-ID or
extraction failures still outstanding, the score distribution, and the paths to
the CSV and its legend.

Do not run the cheat checks unless asked. They are a separate workflow with a
separate purpose — see `references/workflows/grade/cheat_check.md`.
