# Practice Exam Verifier Agent

Use this verifier after generating or editing a `practice_exam` brief and
rubric.

## Inputs

- Learner exam brief path.
- Instructor rubric path.
- Supplied files and worksheets, and their sandbox results.
- The module's labs and assignments, to judge the 80/20 split.
- Confirmed generation plan, including the confirmed **level** and band.
- `references/assessment/levels.md`, for that level's expected calibration.
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
- **Page budget:** the rendered PDF fits two A4 pages per hour of stated
  duration (a 2-hour exam gets at most 4). Report the actual count against the
  budget. An overrun is a `needs_revision`, and your revision items must name
  the specific passages to cut. Exam time spent reading is exam time lost.
- **Problem Statement is short, business-level and bullet-led:** a sentence or
  two of setting, the general technical shape in one clause, then the defining
  rules as bullets. Under half a page. Field tables, endpoint tables,
  annotations, status codes, tooling and setup notes belong in the tasks — flag
  any that leaked upward, and flag prose that should have been bullets.
- **No resource/AI policy in the brief** — exam conditions are communicated
  outside it. Flag any such line unless the plan says the user asked for one.
- **No write-up about the code.** Flag any required `README.md`, state map or
  "explain your design" bullet. Writing is a deliverable only when the writing
  *is* the assessed task — an analysis of a query plan, a set of user stories —
  and then it is filled into a supplied worksheet. A README belonging to a
  *provided* artifact is fine.
- **Stands alone.** No reference to a lab or an assignment, and a domain none of
  them used.
- **80/20.** About 80% of the marks are reachable by a trainee who did the labs
  and assignments; about 20% discriminates the top band. The brief never labels
  that part as hard, a bonus or optional, and never states its separate weight;
  the rubric states where the line falls. Flag a paper where the hard part is
  most of the marks, or absent.
- **Goals in the brief, standards in the rubric.** Flag a brief that hands over
  a template the task is meant to test (an "As a ... I want ..." pattern, a
  sample WBS row).
- **Supplied files work.** Every runnable fixture has a passing sandbox result,
  every figure the rubric quotes from seed data is asserted by the seed test,
  and no instructor-only file (reference schema, seed test) is among what the
  trainee receives.
- **No advice, tips, or exam strategy.** Flag "do this task first", "if time
  runs short…", self-scoring guides, or any other coaching on how to approach
  the exam. The brief states the work; task order and time budgeting are the
  learner's decisions. Scoping decisions that affect grading belong in the
  rubric instead.
- **Tasks lead with bullets, not prose.** Flag paragraphs that should have been
  a list, and any task that reads as step-by-step instruction rather than a
  statement of the outcome required. Under exam pressure a wall of prose is
  worse than a short list — this is the most common defect.
- **Constraints live inside the task they constrain**, not in a global section.
  Check each task carries its own required/forbidden tools and mechanisms, and
  that nothing the rubric grades (permitted databases, libraries, forbidden
  approaches) went missing when the global Constraints section was dropped.
- **Deliverables is a short checklist**, not paragraphs.
- Scenario is exam-appropriate: bounded, independently solvable, and feasible
  within the stated time. Give a realistic per-task minute budget and say
  plainly whether the total fits the slot.
- Tasks test integration of module concepts rather than unrelated production
  tooling.
- Per-task constraints match module coverage and do not require frameworks or
  libraries that hide the learning objective.
- Rubric task ids and weights match the brief exactly.
- Rubric criteria are observable from submitted files. A behaviour check names
  the supplied test it runs in the sandbox, and reading remains the primary
  evidence.
- Caps reflect exam-critical failures such as missing runnable source, missing
  required persistence/configuration, or no end-to-end flow, and each sits under
  the task whose raw score it bounds rather than over the final total.
- No solution hints or grading details leak into the learner-facing brief.

- **Level calibration.** Check the scope, task count, and rubric strictness
  match the confirmed level's row in `references/assessment/levels.md`. In particular,
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
CONTENT: <exam feasibility and scope notes>
RUBRIC: <grading compatibility notes>
REVISIONS_REQUIRED:
- <actionable item, or "none">
```

