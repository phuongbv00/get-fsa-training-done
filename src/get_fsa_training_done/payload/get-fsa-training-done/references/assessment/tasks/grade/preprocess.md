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
   `.git` is kept: for a Git task the history is the evidence.

   **A submitted `.git` is untrusted.** Its config can name programs git runs
   on this machine — an external diff, a textconv filter, an fsmonitor hook, a
   pager. Read history only between commits, never against the working tree,
   and only with those switched off:

   ```bash
   git -c core.fsmonitor= -c core.hooksPath=/dev/null --no-pager log --graph --all --oneline --decorate
   git -c core.fsmonitor= -c core.hooksPath=/dev/null --no-pager show --no-ext-diff --no-textconv <commit>
   git -c core.fsmonitor= -c core.hooksPath=/dev/null --no-pager diff --no-ext-diff --no-textconv <commit> <commit>
   ```

   No `status`, `checkout`, `diff` against the working tree, or any command
   that writes: those run the repository's filters and hooks.
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
