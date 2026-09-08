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

## 2. Criteria must be checkable without running anything

Grading reads the submitted files as evidence and **never executes learner
code**. Phrase every full-mark description as something observable: a file that
exists, a query that has a particular shape, a class that uses a particular
mechanism. "Works correctly" is not checkable; "every user-supplied value is
bound through a PreparedStatement, with no string-concatenated SQL" is.

The brief may state only the outcome while the rubric names the mechanism — see
`levels.md`, where how much the brief may give away depends on the level. When
it does, make sure the named mechanism is a realistic way to satisfy the
outcome, and phrase it so an equally valid alternative is not punished.

## 3. Caps and deductions are folded into task scores

There is no separate adjustment step. A cap is an absolute maximum for that
task, the lowest applicable cap wins, and caps are never additive. Deductions
apply after caps and the result is floored at zero. All of it lands inside the
task score it belongs to, so the score sheet needs no `bonus` or `adjustments`
field.

## 4. The submission archive name carries the roster id

Preprocessing matches each uploaded archive against the roster's `ID` column, so
when the deliverable is a single archive, require:

```
<StudentID>_<subject_lower>_<archive_token>_<seq>.zip
```

and say plainly that `<StudentID>` is exactly their id on the class roster, with
a concrete example (`PhuongBV3_jpl_p_exam_02.zip`).

The `<archive_token>` is **not** the artifact's type token:

| `assessment_type` | archive token |
|---|---|
| `quiz` | `quiz` |
| `short_assignment`, `long_assignment` | `assignment` |
| `theory_exam` | `t_exam` |
| `practice_exam` | `p_exam` |
| `capstone_project` | `capstone` |

So `jpl_practice_exam_02.md` asks for `<StudentID>_jpl_p_exam_02.zip`.

Never use a vague placeholder like `<your_name>` or `<your_account>`. An archive
whose name does not contain the roster id lands in UNKNOWN-ID and has to be
resolved by hand. If the deliverable is a repository rather than an archive, put
the roster id in the repository name instead.

**Avoid roster ids containing underscores.** Folder names are
`<SUBJECT>_<TYPE>_<STDID>`, and while the tooling now strips the known prefix
rather than splitting on the last underscore, an id with an underscore is still
needlessly ambiguous to a human reading the tree.
