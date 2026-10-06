# The design-to-grading contract

Read this when `grade_pipeline` is yes — that is, whenever the assessment you
are designing will actually be collected and marked.

Four things have to line up, or grading breaks in ways that are tedious to
repair by hand.

## 1. The rubric's fixed task list is the scoring structure

Every task in the brief becomes a row in the rubric's `## 2. Fixed Task List`,
and every row becomes an entry in each submission's score sheet:

| Requirement | Why |
|---|---|
| ids are `T1`, `T2`, … in order | the score sheet is keyed by them |
| weights sum to exactly 100% | the total is `sum(score * weight) / 100` |
| names match the brief exactly | the grader cross-checks brief against rubric |
| every sub-criterion table sums to 10.0 | task scores are on a 0-10 raw scale |

## 2. Criteria are settled by reading the submission

Grading reads the submitted files as evidence and **never runs learner code on
the grading machine**. Phrase every full-mark description as something
observable: a file that exists, a query that has a particular shape, a class
that uses a particular mechanism. "Works correctly" is not checkable; "every
user-supplied value is bound through a PreparedStatement, with no
string-concatenated SQL" is.

When behaviour has to be shown, name the check: "the supplied `seed_test.sql`
passes against the submitted `schema.sql`", "the supplied tests pass". The
grader runs it through `FSA assessment sandbox`, in a container with no network,
and the result sits beside what reading found. Reading stays the primary
evidence: a submission that fails to build is still scored for what it contains.

The brief may state only the outcome while the rubric names the mechanism — see
`levels.md`, where how much the brief may give away depends on the level. When
it does, make sure the named mechanism is a realistic way to satisfy the
outcome, and phrase it so an equally valid alternative is not punished.

## 3. Caps and deductions belong to a task, not to the total

There is no separate adjustment step and nothing is ever subtracted from the
final score. The rubric's `## 4. Caps and Deductions` is written as one
subsection per task, and every entry inside it bounds **that task's raw 0-10
score**:

```markdown
## 4. Caps and Deductions

### Every task

| Trigger | Effect |
|---|---:|
| No meaningful source submitted | cap 2.0 |
| Generated output or unrelated large files included | -0.2 |

### T3 - Transactional Stock Adjustment

| Trigger | Effect |
|---|---:|
| No stock-adjustment endpoint is implemented | cap 6.0 |
| The rejected adjustment still writes `updatedAt` | -0.3 |
```

- A cap is an absolute maximum for that task's raw score. The lowest applicable
  cap for a task wins; caps are never additive.
- Deductions apply after the cap, and the task score is floored at zero.
- `### Every task` is the only non-task subsection, it comes first, and it holds
  the failures that leave no task evidenced at all.

`### Every task` costs nothing in reach: deducting `d` from every task's raw
score lowers `sum(score * weight) / 100` by exactly `d`, and capping every task
at `c` caps the total at `c`. What changes is that the score sheet can record it
— the sheet carries task scores and nothing else, so an adjustment made after
weighting cannot be reproduced from the file, and a flat table of `max 5.0` rows
leaves two graders disagreeing about which task each one bounded.

`FSA assessment verify` rejects a rubric with table rows outside a subsection of
section 4, with subsections out of task order, or with a `Caps applied:` /
`Deductions:` line in its score sheet.

## 4. The submission archive name ends with the FPT account

Preprocessing matches each uploaded archive against the roster's `ID` column, so
when the deliverable is a single archive, require:

```
<subject_lower>_<archive_token>_<seq>_<fpt_account>.zip
```

and say plainly that `<fpt_account>` is their FPT account — the same string as
their id on the class roster — with a concrete example
(`jpl_p_exam_02_PhuongBV3.zip`).

The `<archive_token>` is **not** the artifact's type token:

| `assessment_type` | archive token |
|---|---|
| `quiz` | `quiz` |
| `short_assignment`, `long_assignment` | `assignment` |
| `theory_exam` | `t_exam` |
| `practice_exam` | `p_exam` |
| `capstone_project` | `capstone` |

So `jpl_practice_exam_02.md` asks for `jpl_p_exam_02_<fpt_account>.zip`, and
`fnd_practice_exam_01.md` asks for `fnd_p_exam_01_<fpt_account>.zip`.

**The account goes last, and the assessment stem first.** The stem is identical
for everyone, so a folder of uploads sorts by assessment and then by account,
and the account is the one token that varies. It is also what the id matcher
falls back to when nothing matches the roster: it takes the last token, which
under this shape is the account rather than the sequence number.

Never write a vague placeholder like `<your_name>` or `<your_account>` — name
the FPT account explicitly and show an example. An archive whose name does not
contain the roster id lands in UNKNOWN-ID and has to be resolved by hand. If the
deliverable is a repository rather than an archive, put the account in the
repository name instead.

**Avoid roster ids containing underscores.** Folder names are
`<SUBJECT>_<TYPE>_<STDID>`, and while the tooling now strips the known prefix
rather than splitting on the last underscore, an id with an underscore is still
needlessly ambiguous to a human reading the tree.
