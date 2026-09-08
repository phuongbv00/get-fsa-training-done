# Rubric - Clinic Management System

> **Code:** FR_MKP_PRJ_01
> **INSTRUCTOR ONLY — DO NOT distribute to learners.**

## 1. Grading Principle

Grade from the submitted artifacts as evidence. Never execute team code. Every
full-mark description below is something an instructor can observe by reading a
file, a repository at a tag, or a Drive folder listing.

## 2. Fixed Task List

| ID | Task | Weight |
|---|---|---|
| T1 | D01 Project Proposal | 10% |
| T2 | D02 Product Backlog and WBS | 10% |
| T3 | D03 Requirement and Design Documents | 15% |
| T4 | D04 Source Code | 30% |
| T5 | D05 Final Presentation and Demo | 10% |
| T6 | Sprint Process | 10% |
| T7 | Individual contribution | 15% |

## 3. Per-Task Scoring Guide

### T1 - D01 Project Proposal

| Criterion | Points | Full mark |
|---|---|---|
| Scope and actors | 4.0 | Every actor named, and an explicit out-of-scope list |
| Staffing plan | 3.0 | Each member is assigned to named areas across the three sprints |
| Feasibility | 3.0 | Scope stated fits four people and six weeks |
| **T1 raw score** | **10.0** | |

### T2 - D02 Product Backlog and WBS

| Criterion | Points | Full mark |
|---|---|---|
| Story quality | 4.0 | Each story has acceptance criteria a grader could test against |
| WBS depth | 3.0 | Tasks are one-person, one-day units |
| Assignee and estimate | 3.0 | Every task carries both, with no unassigned rows |
| **T2 raw score** | **10.0** | |

### T3 - D03 Requirement and Design Documents

| Criterion | Points | Full mark |
|---|---|---|
| Use cases | 3.0 | Cover every actor in the proposal |
| ERD | 3.0 | Keys and relationships match the schema in the repository |
| Architecture | 2.0 | Components and their protocols are named |
| Diagram-as-code | 2.0 | Sources are committed; no exported images |
| **T3 raw score** | **10.0** | |

### T4 - D04 Source Code

| Criterion | Points | Full mark |
|---|---|---|
| Core features | 4.0 | Booking, confirmation, and result entry all present in the tagged tree |
| Stack compliance | 2.0 | Spring Boot, React, PostgreSQL as mandated |
| Query safety | 2.0 | Every user-supplied value is bound, with no string-concatenated SQL |
| Repository hygiene | 2.0 | README states how to run; no secrets committed |
| **T4 raw score** | **10.0** | |

### T5 - D05 Final Presentation and Demo

| Criterion | Points | Full mark |
|---|---|---|
| Live demo | 4.0 | Run against a running system, not a recording |
| Per-member speaking | 3.0 | Every member presents the part they own |
| Questions | 3.0 | Each member answers a question about their own code |
| **T5 raw score** | **10.0** | |

### T6 - Sprint Process

Raw score is the mean of the per-sprint checkpoint forms, to one decimal place.
Each form scores delivery and dates only; the artifacts themselves are graded in
T1-T5.

| Criterion | Points | Full mark |
|---|---|---|
| Backlog integrity, G1 | 2.5 | Both snapshots present; closing statuses reconcile with the tagged tree |
| Delivery on the tag, G2 | 2.5 | Annotated tag on the default branch, pushed before the deadline |
| Submission completeness, G3 | 1.5 | Every required file in the folder, named exactly, before the deadline |
| Review record, G4 | 1.5 | Done and not-done reconcile with the closing backlog; per-member lines name task ids |
| Sprint deliverable, G5 | 2.0 | The artifact that sprint owns is present and reviewable |
| **T6 raw score** | **10.0** | |

### T7 - Individual contribution

| Criterion | Points | Full mark |
|---|---|---|
| Commit history | 4.0 | Commits under their own account across at least three of the five deliverable areas |
| Review record lines | 3.0 | Named task ids in every sprint review record |
| Defence | 3.0 | Presented their own part and answered a question about their own code |
| **T7 raw score** | **10.0** | |

## 4. Caps and Deductions

Absolute maxima for the task named. The lowest applicable cap wins, and caps are
never additive. Deductions apply after caps, floored at zero.

| Trigger | Cap |
|---|---|
| Any gate missed in a sprint | that sprint's checkpoint raw score capped at 5.0 |
| G1 missed in half the sprints or more | T2 capped at 5.0 |
| G2 missing, or tagged after the deadline, in any sprint | T6 capped at 6.0 |
| G3 missed | the sprint deliverable is graded from what the folder held at the deadline |
| G4 missing in any sprint | T7 capped at 7.0 for every member of that team |
| G5 missed | that checkpoint criterion scores 0 |
| Exported images instead of diagram sources | T3 capped at 6.0 |
| Stack not as mandated | T4 capped at 5.0 |

## 5. Common point-loss reasons

- Backlog written after the work, so the freeze snapshots are identical.
- Tasks with no assignee, which makes individual contribution unreadable.
- Diagrams pasted as PNG with no source committed.
- A demo played from a recording because the deployment broke that morning.
- Review records that say "helped the team" instead of naming task ids.

## 6. Score sheet

One JSON file per member, named by roster id.

| ID | Task | Weight |
|---|---|---|
| T1 | | 10% |
| T2 | | 10% |
| T3 | | 15% |
| T4 | | 30% |
| T5 | | 10% |
| T6 | | 10% |
| T7 | | 15% |
