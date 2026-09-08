# Workflow — long assignment (3+ days)

Multi-day work built over several sittings. Everything from
`short_assignment.md` applies; this file covers only what differs.

**Produces:** `<stem>.md`, `<stem>_rubric.md`, `<stem>.pdf`

Read `references/workflows/design/short_assignment.md` first for the brief and
rubric shape, then apply the differences below.

## What changes

### Banner and code

`Code: <LEVEL>_<SUBJ>_LA_<seq>`, and `Duration:` is expressed in days or weeks
("5 days", "2 weeks").

### No page budget

The two-pages-per-hour rule exists because a trainee reads an exam brief inside
the exam. Over several days that constraint is meaningless, so `FSA assessment render`
reports the page count and enforces nothing.

That removes the pressure that keeps a brief short, so hold the line yourself:
the brief is still a specification, not a tutorial. If it runs past three pages,
you are probably explaining how instead of stating what.

### Tasks become milestones

Order the tasks so they can be built in sequence, each leaving something that
runs. A trainee who gets two-thirds of the way through should have a working
subset, not a half-wired whole. Say so in the task order; do not add a schedule.

Still no advice about pacing. "Task 3 depends on the schema from Task 1" is
structure; "aim to finish Task 1 by day two" is strategy, and belongs nowhere.

### A larger deliverable set is allowed

Multi-day work can reasonably ask for a repository rather than an archive, and
for a migration or seed script alongside the source. It still must not ask for
written explanation — the no-README rule holds, for the same reason.

If the deliverable is a repository, the roster id goes in its name (see
`references/grading_contract.md`).

### Scope, by level

The level's `duration_factor` in `references/levels.md` scales the baseline you
would set for a fresher. Take the task count from the level's range, and let the
extra days buy *depth* — more demanding correctness, harder edge cases, real
failure modes — rather than more features. A long assignment that is just a
short one with six more CRUD endpoints tests stamina, not skill.

## Verify

```bash
FSA assessment render "<output_dir>/<stem>.md"
FSA assessment verify --type long_assignment \
  --brief  "<output_dir>/<stem>.md" \
  --rubric "<output_dir>/<stem>_rubric.md" \
  --pdf    "<output_dir>/<stem>.pdf" \
  --level  "<LEVEL>"
```

`--level` takes the band with it for the banded levels — `UP_SKILL:mid`,
`RE_SKILL:senior` — and the level alone for `CPL` and `FR`.

Then run `references/verifiers/long_assignment.md`.
