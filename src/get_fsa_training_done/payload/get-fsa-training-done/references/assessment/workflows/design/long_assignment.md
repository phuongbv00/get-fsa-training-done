# Workflow — long assignment (3+ days)

Multi-day work built over several sittings.

**Produces:** `<stem>.md`, `<stem>_rubric.md`, `<stem>.pdf`, and any supplied files.

| Step | Task | For a long assignment |
|---|---|---|
| 1 | `references/assessment/tasks/design/plan_scope.md` | scope by the level's `duration_factor`, below |
| 2 | `references/assessment/tasks/design/write_brief.md` | `Code: <LEVEL>_<SUBJ>_LA_<seq>`; Duration in days or weeks; tasks as milestones, below |
| 3 | `references/assessment/tasks/design/write_rubric.md` | the level's rubric posture |
| 4 | `references/assessment/tasks/design/build_fixtures.md` | a mock API or starter the assignment depends on; it must run on its own, with tests |
| 5 | `references/assessment/tasks/design/render_pdf.md` | no page budget; past three pages, cut |
| 6 | `references/assessment/tasks/design/verify.md` | `--type long_assignment`; verifier `references/assessment/verifiers/long_assignment.md` |

## What is particular to a long assignment

**Tasks are milestones.** Order them so they build in sequence, each leaving
something that runs: a trainee two-thirds through has a working subset, not a
half-wired whole. "Task 3 depends on the schema from Task 1" is structure; "aim
to finish Task 1 by day two" is strategy, and belongs nowhere.

**Self-contained.** If the assignment calls an API, supply one the trainee can
run locally rather than depending on another assignment's server.

**A repository deliverable is allowed**, with the FPT account in its name (see
`references/assessment/grading_contract.md`), and a migration or seed script
beside the source. Still no README or write-up about the code.

**Scope, by level.** The level's `duration_factor` in
`references/assessment/levels.md` scales the baseline for a fresher. Let the
extra days buy *depth* — harder edge cases, real failure modes — rather than
more features. A long assignment that is a short one with six more CRUD
endpoints tests stamina, not skill.
