# Project Spec - Clinic Management System

> **Code:** FR_MKP_PRJ_01
> **Level:** FR

## Team size

Four members per team. Teams are assigned by the instructor and balanced on
entry scores.

## Duration

6 weeks, 2026-09-01 to 2026-10-12. The defence is on 2026-10-15.

## Sprints

| Sprint | Start | End | Deliverables due |
|---|---|---|---|
| 1 | 2026-09-01 | 2026-09-14 | D01, D02 |
| 2 | 2026-09-15 | 2026-09-28 | D03 |
| 3 | 2026-09-29 | 2026-10-12 | D04, D05 |

## Sprint checkpoint

At the end of every sprint the team must clear all 5 gates below
before **23:59 on the sprint's last day** in the `## Sprints` table.
A missed gate is capped under `## 4. Caps and Deductions` in the rubric.

`<N>` is the sprint number, 1 to 3.

### G1 - Backlog freeze

Freeze the backlog **before** the sprint starts and export it as
`backlog_sprint<N>_open.csv`; export it again at the end as
`backlog_sprint<N>_close.csv`. Use `backlog_template.csv` for the columns.

- Every task has **exactly one** Assignee and an Estimate. A task nobody owns is
  a task nobody planned, and it counts as missing.
- Tasks added after the freeze are allowed, but must carry
  `Added <YYYY-MM-DD>` in the `Note` column and appear in the G4 record as a
  scope change.
- The `Status` column accepts only: `Todo`, `Doing`, `Done`, `Carried over`.

### G2 - Code tag

Create an annotated tag on the default branch and push it before the
deadline:

```bash
git tag -a sprint-<N> -m "Sprint <N>: <scope summary>"
git push origin sprint-<N>
```

- **The tag date is the proof you delivered on time.** A tag created after the
  deadline is late, however long ago the code was written.
- Do not upload source code to Drive. The tag is the code submission.
- The repository must be reachable by the instructor's account when it is
  marked.

### G3 - Submission folder

Submit to this Google Drive path, exactly:

`MKP-F26/<TEAM>/Sprint <N>/`

Contents, with these filenames:

| File | From gate |
|---|---|
| `backlog_sprint<N>_open.csv` | G1 |
| `backlog_sprint<N>_close.csv` | G1 |
| `sprint<N>_review.md` | G4 |
| That sprint's deliverable | G5 |

**The Drive upload time is the submission time.** Files edited after the
deadline are not read — what gets marked is what the folder held at 23:59
on the sprint's last day.

### G4 - Sprint review record

Write `sprint<N>_review.md` **during the sprint review**, not after.
Use `sprint_review_template.md` for the shape. The record needs a date and every
member's name.

The per-member section is the primary evidence for the individual mark. Name
task ids and the actual code — "helped the team" cannot be graded.

### G5 - Sprint deliverable

The deliverable that sprint owns, per the sprint schedule above. Each
deliverable's own rules — diagram-as-code, the `docs/` layout, submission format
— are in the brief's Deliverables section and apply here unchanged.

## Stack

Mandatory: Java 21 with Spring Boot, React, PostgreSQL. The UI library, the
validation library, and the CI tooling are the team's choice.

## Demo

45 minutes per team: 20 minutes of live demo, 25 minutes of questions. Every
member presents the part they own and answers questions about that code.

## Contribution

Measured from commit history, the per-member lines in the sprint review records,
and the part each member presents at the defence. The individual mark is 15% of
the final grade and is not capped by the team's mark.
