# Long Assignment Verifier Agent

Use this verifier after generating or editing a `long_assignment` brief and
rubric — work spread over three or more days.

## Inputs

- Learner brief path.
- Instructor rubric path.
- Confirmed generation plan, including the confirmed **level** and band.
- `references/levels.md`, for that level's expected calibration.
- Structural verifier output.
- Rendered brief PDF path and its page count.
- Relevant lecture/topic scope.

## Verification Focus

Check both structure and content:

- Brief follows the three-section long-form structure: title, then a header
  banner carrying **only** `Code:`, `Duration:` and `Topics:`, then
  **1. Problem Statement, 2. Tasks, 3. Deliverables**. The retired Context &
  Objective / Prerequisites / Constraints sections must not reappear, and no
  extra banner lines may be added.
- **No page budget applies** — the duration is measured in days, so the
  two-pages-per-hour rule is meaningless and nothing enforces brevity. Judge it
  yourself: the brief is a specification, not a tutorial. Report the page count,
  and if it runs past about three pages say where it is explaining *how* instead
  of stating *what*.
- **Tasks are milestones.** Check they can be built in sequence, each leaving
  something that runs, so a learner two-thirds through has a working subset
  rather than a half-wired whole. Flag ordering that forces everything to land
  at once. Dependencies between tasks are structure and belong in the brief;
  pacing advice ("aim to finish Task 1 by day two") is strategy and does not.
- **The extra days buy depth, not breadth.** Flag a long assignment that is a
  short one with more CRUD endpoints bolted on — that tests stamina, not skill.
  The additional scope should raise the correctness bar, the edge cases, or the
  failure modes.
- **Problem Statement is short, business-level and bullet-led:** a sentence or
  two of setting, the general technical shape in one clause, then the defining
  rules as bullets. Under half a page. Field lists, endpoint tables,
  annotations, status codes, tooling and setup notes belong in the tasks — flag
  any that leaked upward, and flag prose that should have been bullets.
- **No resource/AI policy in the brief** — conditions are communicated outside
  it. Flag any such line unless the plan says the user asked for one.
- **No written deliverable.** Flag any required `README.md`, state map, design
  rationale, or "explain your choice" bullet unless the user explicitly asked
  for one — assessments grade code only. Confirm no rubric criterion depends on
  prose the learner must write, and that removing one did not leave a per-task
  raw-point table off 10.0.
- **No advice, tips, or work strategy.** Flag "do this task first", "if time
  runs short…", self-scoring guides, or any other coaching on how to approach
  the assignment. Scoping decisions that affect grading belong in the rubric.
- **Tasks lead with bullets, not prose.** Flag paragraphs that should have been
  a list, and any task that reads as step-by-step instruction rather than a
  statement of the outcome required.
- **Constraints live inside the task they constrain**, not in a global section.
  Check each task carries its own required/forbidden tools and mechanisms, and
  that nothing the rubric grades (permitted databases, libraries, forbidden
  approaches) went missing when the global Constraints section was dropped.
- **Deliverables is a short checklist**, not paragraphs.
- Brief stays learner-facing: no answer key, no grading judgement calls beyond
  task weights, no rubric-only details.
- Task headings and weights are clear, sum to 100%, and are appropriate for an
  assignment workload.
- Required tools and constraints are covered by the module lectures; do not
  require technologies outside the taught scope.
- Rubric is instructor-only, uses matching `T1..Tn` ids and weights, and gives
  observable evidence for each criterion.
- Per-task raw-point tables sum to 10.0 and can be applied by both a human
  grader and an LLM reviewing submitted files.
- Caps and deductions cover critical failure modes without double-counting
  ordinary missing features.
- Deliverables are concrete and do not over-specify submission transport unless
  the user explicitly asked for it.

- **Level calibration.** Check the scope, task count, and rubric strictness
  match the confirmed level's row in `references/levels.md`. In particular,
  whether the brief may name mechanisms is a property of the level: at
  `UP_SKILL` and above the brief should state outcomes and let the candidate
  choose the mechanism, while the rubric still names it so criteria stay
  observable. Flag a brief that gives away the approach at a level that should
  not.

## Output

Return:

```text
VERDICT: pass | needs_revision
STRUCTURE: <brief notes>
CONTENT: <scope/quality notes>
RUBRIC: <grading compatibility notes>
REVISIONS_REQUIRED:
- <actionable item, or "none">
```

