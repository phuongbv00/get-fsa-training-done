# Task — Preprocess submissions

Turn a folder of raw uploads into one clean folder per trainee.

## Inputs

| Input | Notes |
|---|---|
| `roster` | CSV with `ID`, `Name`, `Status` columns |
| `submissions_dir` | the raw uploads; never modified |
| `subject`, `submission_type` | e.g. `DBF`, `P_EXAM` |

Suggest a conventional path only when it already exists under a directory the
user named.

## Produces

`<submissions_dir>/_preprocessed/<SUBJECT>_<TYPE>_<STDID>/` per trainee, and a
report.

## Steps

1. Run:

   ```bash
   FSA assessment grade preprocess --roster "<roster>" --src "<submissions_dir>" \
     --subject "<SUBJECT>" --type "<TYPE>" --out "<submissions_dir>/_preprocessed"
   ```

   It extracts archives and strips junk and redundant nesting. A repository's
   `.git` is kept: for a Git task the history is the evidence. Read it with
   read-only commands (`git log --graph --all`, `git show`, `git diff`).
2. Resolve what the report flags:
   - **UNKNOWN-ID** — the filename matched no roster id; usually a renamed
     archive. Resolve by hand.
   - **Did NOT submit** — confirm with the user rather than assuming a zero.
   - **Extraction FAILED** — a corrupt or unusual archive; `FSA doctor` lists
     the extractors this machine has.

## Done when

Every roster trainee is either a folder, a confirmed non-submission, or a named
open issue.

## Hands off to

`references/assessment/tasks/grade/plan_batches.md`.
