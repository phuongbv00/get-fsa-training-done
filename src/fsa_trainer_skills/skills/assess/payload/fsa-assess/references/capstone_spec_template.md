# Capstone project spec template

A capstone brief describes the *product*. This spec pins down everything about
how the work is organised and judged — team size, how long, how many sprints,
what stack, what the demo looks like, and how an individual's contribution is
separated from their team's.

It exists because these are exactly the things that get referred to and never
defined. A deliverables list that says "due in Sprint 1" without anywhere
defining how many sprints there are, or how long one lasts, cannot be graded
consistently.

Written in the same language as the brief — English.

---

```markdown
# Project Spec - <Project name>

> **Code:** <LEVEL>_<SUBJ>_PRJ_<seq>
> **Level:** <LEVEL>

## Team size

<How many members per team, and how teams are formed.>

## Duration

<Total length, the start date, and the defence date.>

## Sprints

| Sprint | Start | End | Deliverables due |
|---|---|---|---|
| 1 | 2026-09-01 | 2026-09-14 | D01, D02 |
| 2 | 2026-09-15 | 2026-09-28 | D03 |
| 3 | 2026-09-29 | 2026-10-12 | D04, D05 |

<One row per sprint. Dates in ISO 8601. Each of D01-D05 appears in exactly
one sprint.>

## Sprint checkpoint

<Leave this heading empty. `FSA sprint-kit --update-spec` generates the five
gates G1-G5 here, from the same source as the learner handout.>

## Stack

<Mandatory language, framework, and database. State clearly what is free choice.>

## Demo

<Length of the defence, its structure (demo / questions), and the requirement
that every member presents the part they own.>

## Contribution

<What individual contribution is measured from: commit history, sprint review
records, the part presented at the defence. State how the individual mark
affects the final grade.>
```

---

## Required sections

`FSA verify --type capstone_project --spec …` checks that all seven are present.
Each corresponds to something the deliverables refer to:

| Section | What refers to it |
|---|---|
| Team size | group deliverables and per-member contribution |
| Duration | the whole schedule |
| Sprints | every "due in Sprint N" line |
| Sprint checkpoint | the rubric's gate caps, and the sprint-process task |
| Stack | the source-code deliverable |
| Demo | the final presentation deliverable |
| Contribution | the rubric's individual-contribution task |

## The sprint table is parsed, not just read

`Sprints` is the one section with a fixed shape, because five separate checks
depend on being able to read it:

- sprint numbers run `1..N` with no gaps and no repeats;
- dates are ISO 8601, each sprint ends after it starts, and sprint `N+1` starts
  after sprint `N` ends;
- each of `D01`–`D05` is due in **exactly one** sprint — a deliverable in no
  sprint can never be late, and one in two sprints has two deadlines;
- every `Sprint N` the brief or rubric mentions is a sprint this table has;
- when there are two or more sprints, the rubric needs a sprint-process task
  for the checkpoint scores to land in.

Keep the columns in the order shown. The parser reads them positionally.

## Why contribution is mandatory

Without a task that scores the individual, every member of a team receives the
team's mark regardless of what they did. The verifier treats a rubric with no
contribution task as an error, not a warning.
