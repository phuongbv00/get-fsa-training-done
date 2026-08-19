# Capstone Project Verifier Agent

Use after generating or editing a capstone brief, spec, and rubric.

`FSA verify --type capstone_project` has already checked that the six spec
sections exist, that D01–D05 each map to exactly one task, that an
individual-contribution task exists, and that the weights sum to 100%. **Do not
re-check those.** Judge whether the thing is actually gradable and actually
buildable.

## Inputs

- Brief, spec, and rubric paths, plus the rendered PDF.
- Confirmed generation plan, including the confirmed **level** and band.
- `references/levels.md`, for that level's expected calibration.
- `FSA verify` output.

## Verification focus

### Scope fits the team and the time

The spec states a team size and a number of sprints. Give a realistic estimate
of the core scope in person-days and say plainly whether it fits. Capstone
briefs fail far more often by being too large than too small, and an
over-scoped project produces rushed work that grades badly for reasons the
rubric never intended to measure.

Check the bonus work is genuinely optional — its weight should be small enough
that a team ignoring it can still score well. A "bonus" carrying 30% is
mandatory work under a friendlier name.

### The individual can be separated from the team

T6 scores the person. Read its full-mark evidence and ask whether two graders
looking at the same team would give the same member the same number. "Đóng góp
tích cực" is not gradable; "commits across at least three of the five
deliverable areas, and presented that part at the defence" is.

Then check the team tasks do not quietly double-count individual work, and that
a strong member on a weak team is not capped by their team's artifacts alone.

### Process criteria have dated evidence

Where a criterion is about how the team worked — backlog, sprint reviews, the
WBS — the evidence must be something with a timestamp. A backlog written the
night before the defence satisfies a criterion that asks only for a backlog to
exist, and satisfies nothing that asks for it to have guided the work.

### The stack constraint is enforceable

The spec mandates a stack. Check the rubric can actually tell whether it was
followed by reading the repository, and that the brief does not simultaneously
invite a choice the spec forbids.

### The demo is scored on something

If D05 carries weight, the rubric needs criteria a grader can apply while
watching a defence — not just "presented well". Per-member speaking, a working
live demo rather than a recording, the ability to answer a question about their
own code.

### Deliverable rules are stated where they bite

Diagram-as-code, the public repository, the `docs/` layout: these belong in the
deliverable bullets the team reads, not only in the rubric that grades them.
Flag any rule the rubric penalises that the brief never states.

### Level calibration

Check the scope, ambiguity, and rubric strictness match the level's row in
`references/levels.md`. A capstone at `CPL` should be guided; one at `UP_SKILL
senior` should require architectural decisions the team has to defend.

### Language

Brief and spec in Vietnamese, rubric in English. Domain terms — Problem
Statement, Scope of Work, backlog, sprint — stay English inside Vietnamese
prose, matching the existing project material.

## Output

```text
VERDICT: pass | needs_revision
STRUCTURE: <brief, spec, and rubric shape notes>
CONTENT: <scope feasibility, with a person-day estimate against team size and duration>
RUBRIC: <gradability, especially the individual-contribution task>
REVISIONS_REQUIRED:
- <actionable item, or "none">
```
